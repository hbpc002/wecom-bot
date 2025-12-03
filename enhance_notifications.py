"""
增强发送按钮的提示功能
确保用户能看到清晰的反馈
"""

def enhance_send_notifications():
    """修改app.js添加更明显的提示"""
    file_path = 'static/js/app.js'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 找到sendToWecom函数并增强提示
    old_function = '''async function sendToWecom(env) {
    const dateInput = document.getElementById('wecomDate');
    const date = dateInput.value;

    if (!date) {
        alert('请选择日期');
        return;
    }

    const btn = env === 'test' ? document.getElementById('sendTestBtn') : document.getElementById('sendProdBtn');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span>⏳</span> 发送中...';

    try {
        const response = await fetch('/api/send-to-wecom', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ date, env })
        });

        const data = await response.json();

        if (data.success) {
            alert(data.message);
        } else {
            alert('发送失败：' + data.error);
        }
    } catch (error) {
        console.error('发送失败:', error);
        alert('发送失败：' + error.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}'''

    new_function = '''async function sendToWecom(env) {
    const dateInput = document.getElementById('wecomDate');
    const date = dateInput.value;

    if (!date) {
        alert('❌ 请先选择日期');
        return;
    }

    const envName = env === 'test' ? '测试环境' : '生产环境';
    
    // 开始前确认（生产环境）
    if (env === 'prod') {
        if (!confirm(`⚠️ 确定要发送到生产环境吗？\\n\\n日期: ${date}\\n环境: ${envName}`)) {
            console.log('用户取消了发送到生产环境');
            return;
        }
    }
    
    const btn = env === 'test' ? document.getElementById('sendTestBtn') : document.getElementById('sendProdBtn');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span>⏳</span> 发送中...';
    
    console.log(`开始发送到${envName}，日期: ${date}`);

    try {
        const response = await fetch('/api/send-to-wecom', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ date, env })
        });

        console.log('收到响应:', response.status);
        const data = await response.json();
        console.log('响应数据:', data);

        if (data.success) {
            alert(`✅ ${data.message}`);
            console.log('发送成功:', data.message);
        } else {
            alert(`❌ 发送失败：${data.error}`);
            console.error('发送失败:', data.error);
        }
    } catch (error) {
        console.error('发送异常:', error);
        alert(`❌ 发送失败：${error.message}\\n\\n请检查网络连接或查看控制台了解详情`);
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
        console.log('发送操作结束');
    }
}'''

    if old_function in content:
        content = content.replace(old_function, new_function)
        print("✓ 已增强sendToWecom函数的提示功能")
        print("  - 添加了console.log调试信息")
        print("  - 增强了alert提示的可见性（添加emoji）")
        print("  - 为生产环境添加了确认对话框")
        print("  - 添加了日期和环境信息显示")
    else:
        print("✗ 未找到sendToWecom函数，可能已经被修改")
        return False
    
    # 移除生产按钮的旧confirm（因为已经移到函数内部）
    old_prod_btn = '''// 发送到企业微信 - 生产环境
document.getElementById('sendProdBtn').addEventListener('click', async () => {
    if (!confirm('确定要发送到生产环境吗？')) {
        return;
    }
    await sendToWecom('prod');
});'''

    new_prod_btn = '''// 发送到企业微信 - 生产环境
document.getElementById('sendProdBtn').addEventListener('click', async () => {
    await sendToWecom('prod');
});'''

    if old_prod_btn in content:
        content = content.replace(old_prod_btn, new_prod_btn)
        print("✓ 已移除生产按钮的重复确认对话框")
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n已更新 {file_path}")
    return True


if __name__ == '__main__':
    print("=" * 60)
    print("增强发送按钮提示功能")
    print("=" * 60)
    print()
    
    if enhance_send_notifications():
        print()
        print("=" * 60)
        print("完成！")
        print("=" * 60)
        print()
        print("【新增功能】")
        print("1. ✅ 所有alert都添加了emoji图标（更醒目）")
        print("2. 📝 添加了console.log调试信息")
        print("3. ⚠️  生产环境发送前会显示确认对话框")
        print("4. 📊 确认对话框显示日期和环境信息")
        print("5. 🔍 所有操作都会在控制台输出日志")
        print()
        print("【测试方法】")
        print("1. 刷新浏览器页面（Ctrl+F5 强制刷新）")
        print("2. 打开开发者工具（F12）查看Console")
        print("3. 选择日期并点击发送按钮")
        print("4. 观察是否有弹窗和控制台日志")
        print()
        print("=" * 60)
    else:
        print("\n修改失败，请检查文件")
