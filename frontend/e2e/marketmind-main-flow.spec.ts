import { expect, test } from "@playwright/test";

test.describe("MarketMind 中文控制台主链路", () => {
  test("用户可以从工作台进入任务、报告、证据链和失败重试", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByRole("heading", { name: "Agent 调研工作台" })).toBeVisible();
    await expect(page.getByRole("link", { name: "新建调研" })).toBeVisible();
    await expect(page.getByText("最近任务")).toBeVisible();
    await expect(page.getByText("最近报告")).toBeVisible();

    await page.getByRole("link", { name: "新建调研" }).click();
    await expect(page.getByRole("heading", { name: "创建竞品调研任务" })).toBeVisible();
    await page.getByLabel("商品 URL 或数据集").fill("demo://e2e-negative-reviews");
    await page.getByRole("button", { name: "创建任务" }).click();
    await expect(page).toHaveURL(/\/tasks\/tsk_9A21$/);
    await expect(page.getByText("任务详情")).toBeVisible();
    await expect(page.getByRole("heading", { name: "便携咖啡机竞品扫描" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Agent 步骤" })).toBeVisible();

    await page.getByRole("link", { name: "任务" }).click();
    await expect(page.getByRole("heading", { name: "调研任务历史" })).toBeVisible();
    await page.getByRole("link", { name: /USB-C/ }).click();
    await expect(page.getByText("任务详情")).toBeVisible();
    await expect(page.getByRole("heading", { name: "USB-C 拓展坞采集任务" })).toBeVisible();
    await expect(page.getByRole("button", { name: "重试任务" })).toBeVisible();
    await page.getByRole("button", { name: "重试任务" }).click();
    await expect(page.getByText("重试任务已提交", { exact: true })).toBeVisible();
    await expect(page.getByText("task.retry_submitted")).toBeVisible();

    await page.getByRole("link", { name: "报告" }).click();
    await expect(page.getByRole("heading", { name: "已生成调研报告" })).toBeVisible();
    await page.getByRole("link", { name: /台灯差评分析/ }).click();
    await expect(page.getByText("报告详情")).toBeVisible();
    await expect(page.getByRole("heading", { name: "台灯差评分析" }).first()).toBeVisible();
    await expect(page.getByRole("heading", { name: "证据引用" })).toBeVisible();

    await page.getByRole("link", { name: "证据链" }).click();
    await expect(page.getByRole("heading", { name: "评论语义检索" })).toBeVisible();
    await expect(page.getByPlaceholder(/搜索质量差/)).toBeVisible();
  });
});
