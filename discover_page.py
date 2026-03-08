from playwright.sync_api import sync_playwright
import os

# 创建截图目录
screenshots_dir = r'e:\PY\CODES\py copilot IV\test_screenshots'
os.makedirs(screenshots_dir, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})

    print("=" * 60)
    print("页面元素发现测试")
    print("=" * 60)

    # 1. 访问首页
    print("\n[1] 访问首页...")
    page.goto('http://localhost:5173')
    page.wait_for_load_state('networkidle')
    
    title = page.title()
    print(f"  页面标题: {title}")
    
    # 获取页面主要文本
    body_text = page.locator('body').inner_text()
    print(f"  页面内容长度: {len(body_text)} 字符")
    print(f"  内容预览: {body_text[:300]}...")
    
    page.screenshot(path=os.path.join(screenshots_dir, 'discover_01_home.png'), full_page=True)
    print("  截图已保存: discover_01_home.png")

    # 2. 发现所有按钮
    print("\n[2] 发现页面上的按钮...")
    buttons = page.locator('button').all()
    print(f"  找到 {len(buttons)} 个按钮:")
    for i, button in enumerate(buttons[:20]):
        try:
            if button.is_visible():
                text = button.inner_text().strip()
                if text:
                    print(f"    [{i}] {text[:50]}")
        except:
            pass

    # 3. 发现所有链接
    print("\n[3] 发现页面上的链接...")
    links = page.locator('a[href]').all()
    print(f"  找到 {len(links)} 个链接:")
    for i, link in enumerate(links[:15]):
        try:
            if link.is_visible():
                text = link.inner_text().strip()[:40]
                href = link.get_attribute('href')
                print(f"    [{i}] {text} -> {href}")
        except:
            pass

    # 4. 导航到设置页面
    print("\n[4] 导航到设置页面...")
    page.goto('http://localhost:5173/settings')
    page.wait_for_load_state('networkidle')
    
    settings_text = page.locator('body').inner_text()
    print(f"  设置页面内容长度: {len(settings_text)} 字符")
    print(f"  内容预览: {settings_text[:500]}...")
    
    page.screenshot(path=os.path.join(screenshots_dir, 'discover_02_settings.png'), full_page=True)
    print("  截图已保存: discover_02_settings.png")

    # 5. 在设置页面发现按钮和链接
    print("\n[5] 设置页面元素...")
    buttons = page.locator('button').all()
    print(f"  按钮数量: {len(buttons)}")
    for i, btn in enumerate(buttons[:15]):
        try:
            if btn.is_visible():
                text = btn.inner_text().strip()
                if text:
                    print(f"    按钮: {text[:40]}")
        except:
            pass

    # 6. 查找并点击模型管理
    print("\n[6] 查找模型管理/供应商管理...")
    
    # 查找包含"模型"或"供应商"的元素
    model_links = page.locator('text=/模型|供应商/i').all()
    print(f"  找到 {len(model_links)} 个相关元素")
    
    for i, elem in enumerate(model_links[:10]):
        try:
            if elem.is_visible():
                text = elem.inner_text().strip()
                print(f"    [{i}] {text}")
                # 点击第一个匹配的元素
                if i == 0:
                    print(f"    点击: {text}")
                    elem.click()
                    page.wait_for_timeout(2000)
                    break
        except Exception as e:
            print(f"    错误: {e}")

    # 7. 截图模型管理页面
    page.screenshot(path=os.path.join(screenshots_dir, 'discover_03_model_mgmt.png'), full_page=True)
    print("  截图已保存: discover_03_model_mgmt.png")

    # 8. 获取模型管理页面内容
    print("\n[7] 模型管理页面内容...")
    model_text = page.locator('body').inner_text()
    print(f"  内容长度: {len(model_text)} 字符")
    print(f"  完整内容:\n{model_text}")

    # 9. 查找测试连接按钮
    print("\n[8] 查找测试连接按钮...")
    test_buttons = page.locator('text=/测试/i').all()
    print(f"  找到 {len(test_buttons)} 个包含'测试'的元素")
    
    for i, btn in enumerate(test_buttons):
        try:
            if btn.is_visible():
                text = btn.inner_text().strip()
                print(f"    [{i}] {text}")
        except:
            pass

    # 10. 查找输入框
    print("\n[9] 查找输入框...")
    inputs = page.locator('input').all()
    print(f"  找到 {len(inputs)} 个输入框")
    for i, inp in enumerate(inputs):
        try:
            placeholder = inp.get_attribute('placeholder') or ''
            input_type = inp.get_attribute('type') or 'text'
            name = inp.get_attribute('name') or ''
            if placeholder or name:
                print(f"    [{i}] type={input_type}, name={name}, placeholder={placeholder}")
        except:
            pass

    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)

    browser.close()
