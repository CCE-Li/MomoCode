import { expect, test } from '@playwright/test'

const password = 'correct horse battery'

test('register, train, analyze, and login again', async ({ page }) => {
  const email = `e2e-${Date.now()}@example.com`

  await page.goto('/register')
  await page.getByLabel('邮箱').fill(email)
  await page.getByLabel('密码', { exact: true }).fill(password)
  await page.getByLabel('确认密码').fill(password)
  await page.getByRole('button', { name: '创建账号' }).click()

  await expect(page).toHaveURL(/\/$/)
  await expect(
    page.getByRole('heading', { name: '训练脉冲' }),
  ).toBeVisible()
  await expect(page.getByText('邮箱尚未验证')).toBeVisible()

  await page.goto('/library')
  await expect(page.getByText('二分查找')).toBeVisible()

  await page.goto('/library/skills/binary-search-recognition')
  await page.getByRole('button', { name: '开始练习' }).click()
  await expect(page.getByText('选择你认为适用的算法')).toBeVisible()
  await page.getByRole('checkbox', { name: /二分查找/ }).check()
  await page.getByRole('button', { name: '提交' }).click()
  await expect(page.getByText('本次证据')).toBeVisible()
  await expect(page.getByText('正确', { exact: true }).first()).toBeVisible()

  await page.goto('/analytics')
  await expect(page.getByText('完成训练', { exact: true })).toBeVisible()
  await expect(page.getByText('正确率').first()).toBeVisible()

  await page.goto('/settings')
  await expect(page.getByText('邮箱未验证').first()).toBeVisible()
  await expect(page.getByText('活跃会话')).toBeVisible()

  await page.getByRole('button', { name: '退出', exact: true }).click()
  await expect(page).toHaveURL(/\/login/)

  await page.getByLabel('邮箱').fill(email)
  await page.getByLabel('密码').fill(password)
  await page.getByRole('button', { name: '登录' }).click()
  await expect(page).toHaveURL(/\/$/)
  await expect(
    page.getByRole('heading', { name: '训练脉冲' }),
  ).toBeVisible()
})

test('account deletion requires typed confirmation', async ({ page }) => {
  const email = `delete-e2e-${Date.now()}@example.com`

  await page.goto('/register')
  await page.getByLabel('邮箱').fill(email)
  await page.getByLabel('密码', { exact: true }).fill(password)
  await page.getByLabel('确认密码').fill(password)
  await page.getByRole('button', { name: '创建账号' }).click()
  await expect(page).toHaveURL(/\/$/)

  await page.goto('/settings')
  await page.getByRole('button', { name: '删除账号' }).click()
  await page.getByLabel('账号密码').fill(password)
  await page.getByLabel('输入 DELETE 确认').fill('DELETE')
  await page.getByRole('button', { name: '永久删除账号' }).click()

  await expect(page).toHaveURL(/\/login/)

  await page.getByLabel('邮箱').fill(email)
  await page.getByLabel('密码').fill(password)
  await page.getByRole('button', { name: '登录' }).click()
  await expect(page.getByRole('alert')).toContainText('邮箱或密码不正确')
})

test('password change and login with new password', async ({ page }) => {
  const email = `password-e2e-${Date.now()}@example.com`
  const newPassword = 'new correct horse battery'

  await page.goto('/register')
  await page.getByLabel('邮箱').fill(email)
  await page.getByLabel('密码', { exact: true }).fill(password)
  await page.getByLabel('确认密码').fill(password)
  await page.getByRole('button', { name: '创建账号' }).click()
  await expect(page).toHaveURL(/\/$/)

  await page.goto('/settings')
  await page.getByLabel('当前密码', { exact: true }).fill(password)
  await page.getByLabel('新密码', { exact: true }).fill(newPassword)
  await page.getByLabel('确认新密码', { exact: true }).fill(newPassword)
  await page.getByRole('button', { name: '更新密码' }).click()
  await expect(page.getByText('密码已更新，其他设备已退出登录。')).toBeVisible()

  await page.getByRole('button', { name: '退出', exact: true }).click()
  await expect(page).toHaveURL(/\/login/)

  await page.getByLabel('邮箱').fill(email)
  await page.getByLabel('密码').fill(newPassword)
  await page.getByRole('button', { name: '登录' }).click()
  await expect(page).toHaveURL(/\/$/)
  await expect(
    page.getByRole('heading', { name: '训练脉冲' }),
  ).toBeVisible()
})
