import { expect, test } from '@playwright/test'

const password = 'correct horse battery'

test('galaxy curtain pulls down from the header and fills the viewport', async ({
  page,
}) => {
  const email = `galaxy-e2e-${Date.now()}@example.com`

  await page.goto('/register')
  await page.getByLabel('邮箱').fill(email)
  await page.getByLabel('密码', { exact: true }).fill(password)
  await page.getByLabel('确认密码').fill(password)
  await page.getByRole('button', { name: '创建账号' }).click()
  await expect(page).toHaveURL(/\/$/)

  const trigger = page.getByRole('button', { name: '星图', exact: true })
  const dialog = page.getByRole('dialog', { name: '记忆星图' })
  await expect(trigger).toBeVisible()
  await expect(dialog).toBeHidden()

  await page.mouse.move(640, 10)
  await page.mouse.down()
  await page.mouse.move(640, 420, { steps: 12 })
  await page.mouse.up()
  await expect(dialog).toBeVisible()

  const box = await dialog.boundingBox()
  expect(box?.width).toBeGreaterThan(1200)
  expect(box?.height).toBeGreaterThan(650)

  await page.mouse.click(640, 690)
  await expect(dialog).toBeHidden()

  await page.mouse.move(640, 300)
  await page.mouse.wheel(0, -360)
  await expect(dialog).toBeVisible()

  await page.getByRole('button', { name: '收起星图' }).click()
  await expect(dialog).toBeHidden()

  await trigger.click()
  await expect(dialog).toBeVisible()
})
