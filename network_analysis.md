# 企业微信机器人网络连接问题分析

## 问题描述
图片生成正常，但发送失败，出现以下错误：
1. `HTTPSConnectionPool(host='qyapi.weixin.qq.com', port=443): Max retries exceeded with url: /cgi-bin/webhook/upload_media?key=...&type=image (Caused by ProxyError('Cannot connect to proxy.', OSError(0, 'Error')))`
2. `{'errcode': 40004, 'errmsg': 'invalid media type, hint: [...], from ip: 121.31.60.243, more info at https://open.work.weixin.qq.com/devtool/query?e=40004'}`

## 问题分析

### 1. 代理错误分析
尽管用户确认没有使用代理，但错误信息显示 `ProxyError('Cannot connect to proxy.', OSError(0, 'Error'))`。这可能是因为：

- Python requests 库在某些情况下会自动检测代理设置
- 可能存在系统级别的代理配置
- 某些安全软件或网络设备可能干扰了网络连接

### 2. 企业微信API调用分析
从代码中可以看到两种不同的API调用：

#### 图片上传API
```python
upload_url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/upload_media?key={self.webhook_url.split('=')[1]}&type=image"
files = {'media': file_obj}
upload_response = requests.post(upload_url, files=files, timeout=10)
```

#### 消息发送API
```python
response = requests.post(self.webhook_url, json=image_message, timeout=10)
```

### 3. 错误模式分析
从日志中可以看到：
- 大部分时间出现代理错误
- 偶尔出现 `invalid media type` 错误
- 有一次成功发送了纯文本消息（行874-875）

## 解决方案

### 方案1：显式禁用代理
在所有requests调用中显式设置proxies为None：

```python
# 在main.py中修改所有requests.post调用
response = requests.post(
    url, 
    data=json_data, 
    files=files, 
    timeout=10,
    proxies=None  # 显式禁用代理
)
```

### 方案2：修复图片上传问题
检查图片文件格式和MIME类型设置：

```python
# 确保正确的MIME类型
files = {
    'media': (os.path.basename(image_path), open(image_path, 'rb'), 'image/jpeg')
}
```

### 方案3：添加重试机制
添加网络重试逻辑处理临时网络问题：

```python
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session_with_retries():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session
```

### 方案4：使用备用发送方式
当图片上传失败时，回退到纯文本消息：

```python
def send_to_wechat_with_fallback(self, report_data):
    try:
        # 尝试发送图片
        if self.send_image_to_wechat(report_data):
            return True
    except Exception as e:
        logging.error(f"图片发送失败: {e}")
    
    # 回退到纯文本
    return self.send_text_to_wechat(report_data)
```

## 推荐实施步骤

1. **立即修复**：在所有requests调用中添加 `proxies=None`
2. **图片格式检查**：确保上传的图片文件格式正确
3. **错误处理改进**：添加更好的错误处理和重试机制
4. **备用方案**：实现图片发送失败时的文本消息备用方案

## 测试验证
- 测试网络连接到 qyapi.weixin.qq.com
- 验证图片文件格式和大小
- 测试修改后的代码是否能正常发送消息