from __future__ import annotations

from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crawler.schemas import CrawlArtifact, CrawlResult, CrawlReview
from app.storage.models import Artifact, CrawledPage, Product, Review, Task


@dataclass(frozen=True, slots=True)
class PersistedCrawlResult:
    product_id: str
    page_id: str
    artifact_ids: list[str]
    review_ids: list[str]


class CrawlResultStore(Protocol):
    def persist_success(self, *, task_id: str, result: CrawlResult) -> PersistedCrawlResult: ...


class SQLAlchemyCrawlResultStore:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def persist_success(self, *, task_id: str, result: CrawlResult) -> PersistedCrawlResult:
        with self._session_scope() as session:
            with session.begin():
                if session.get(Task, task_id) is None:
                    raise ValueError(f"task {task_id} does not exist")

                product = self._upsert_product(session, task_id=task_id, result=result)
                artifacts = [
                    self._upsert_artifact(session, task_id=task_id, artifact=artifact)
                    for artifact in result.artifacts
                ]
                html_artifact_id = _first_artifact_id(artifacts, "crawler_html")
                page = self._upsert_page(
                    session,
                    task_id=task_id,
                    product_id=product.id,
                    result=result,
                    html_artifact_id=html_artifact_id,
                )
                reviews = [
                    self._upsert_review(
                        session,
                        task_id=task_id,
                        product_id=product.id,
                        source_url=result.url,
                        review=review,
                    )
                    for review in result.reviews
                ]
                session.flush()
                return PersistedCrawlResult(
                    product_id=product.id,
                    page_id=page.id,
                    artifact_ids=[artifact.id for artifact in artifacts],
                    review_ids=[review.id for review in reviews],
                )

    @contextmanager
    def _session_scope(self):
        session = self._session_factory()
        try:
            yield session
        finally:
            session.close()

    def _upsert_product(self, session: Session, *, task_id: str, result: CrawlResult) -> Product:
        stmt = select(Product).where(Product.task_id == task_id, Product.source_url == result.url)
        product = session.scalars(stmt).first()
        raw_payload = result.model_dump(
            mode="json",
            exclude={"html", "artifacts", "reviews"},
        )
        if product is None:
            product = Product(
                task_id=task_id,
                title=result.title or "Untitled Product",
                source_url=result.url,
                price=result.price,
                rating=result.rating,
                raw_payload=raw_payload,
            )
            session.add(product)
            session.flush()
            return product

        product.title = result.title or product.title
        product.price = result.price
        product.rating = result.rating
        product.raw_payload = raw_payload
        return product

    def _upsert_artifact(
        self,
        session: Session,
        *,
        task_id: str,
        artifact: CrawlArtifact,
    ) -> Artifact:
        stmt = select(Artifact).where(
            Artifact.task_id == task_id,
            Artifact.artifact_type == artifact.artifact_type,
            Artifact.checksum == artifact.checksum,
        )
        artifact_row = session.scalars(stmt).first()
        metadata = artifact.metadata
        if artifact_row is None:
            artifact_row = Artifact(
                task_id=task_id,
                artifact_type=artifact.artifact_type,
                uri=artifact.path,
                mime_type=artifact.mime_type,
                checksum=artifact.checksum,
                metadata_=metadata,
            )
            session.add(artifact_row)
            session.flush()
            return artifact_row

        artifact_row.uri = artifact.path
        artifact_row.mime_type = artifact.mime_type
        artifact_row.metadata_ = metadata
        return artifact_row

    def _upsert_page(
        self,
        session: Session,
        *,
        task_id: str,
        product_id: str,
        result: CrawlResult,
        html_artifact_id: str | None,
    ) -> CrawledPage:
        stmt = select(CrawledPage).where(
            CrawledPage.task_id == task_id,
            CrawledPage.source_url == result.url,
        )
        page = session.scalars(stmt).first()
        raw_payload = {
            "source_type": result.source_type,
            "fetched_at": result.fetched_at.isoformat(),
            "metadata": result.metadata,
        }
        if page is None:
            page = CrawledPage(
                task_id=task_id,
                product_id=product_id,
                source_url=result.url,
                html_artifact_id=html_artifact_id,
                extracted_text=result.extracted_text,
                raw_payload=raw_payload,
            )
            session.add(page)
            session.flush()
            return page

        page.product_id = product_id
        page.html_artifact_id = html_artifact_id
        page.extracted_text = result.extracted_text
        page.raw_payload = raw_payload
        return page

    def _upsert_review(
        self,
        session: Session,
        *,
        task_id: str,
        product_id: str,
        source_url: str,
        review: CrawlReview,
    ) -> Review:
        external_id = review.external_id or _build_review_external_id(
            task_id=task_id,
            product_id=product_id,
            source_url=source_url,
            content=review.content,
        )
        stmt = select(Review).where(
            Review.product_id == product_id,
            Review.external_id == external_id,
        )
        review_row = session.scalars(stmt).first()
        review_source_url = review.source_url or source_url
        if review_row is None:
            review_row = Review(
                product_id=product_id,
                task_id=task_id,
                external_id=external_id,
                source_url=review_source_url,
                source_type="crawler",
                rating=review.rating,
                content=review.content,
                raw_payload=review.model_dump(mode="json"),
            )
            session.add(review_row)
            session.flush()
            return review_row

        review_row.source_url = review_source_url
        review_row.rating = review.rating
        review_row.content = review.content
        review_row.raw_payload = review.model_dump(mode="json")
        return review_row


def _first_artifact_id(artifacts: list[Artifact], artifact_type: str) -> str | None:
    for artifact in artifacts:
        if artifact.artifact_type == artifact_type:
            return artifact.id
    return None


def _build_review_external_id(
    *,
    task_id: str,
    product_id: str,
    source_url: str,
    content: str,
) -> str:
    digest = sha256(f"{task_id}:{product_id}:{source_url}:{content}".encode()).hexdigest()
    return f"hash_{digest[:24]}"
