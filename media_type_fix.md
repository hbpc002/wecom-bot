# 企业微信图片上传"invalid media type"错误专项修复

## 错误分析
错误信息：`{'errcode': 40004, 'errmsg': 'invalid media type, hint: [1763622786547531266025692]'`

根据企业微信官方文档，错误码40004表示"不合法的媒体文件类型"。

## 企业微信图片上传API要求

### 1. 支持的图片格式
- PNG格式：MIME类型 `image/png`
- JPG格式：MIME类型 `image/jpeg`

### 2. 文件大小限制
- 图片文件大小不能超过2MB

### 3. 上传接口要求
```
POST https://qyapi.weixin.qq.com/cgi-bin/webhook/upload_media?key=KEY&type=image
Content-Type: multipart/form-data
```

## 当前代码问题分析

在main.py第237-241行的代码：
```python
upload_url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/upload_media?key={self.webhook_url.split('=')[1]}&type=image"

file_obj = open(image_path, 'rb')
files = {'media': file_obj}
upload_response = requests.post(upload_url, files=files, timeout=10)
```

**问题**：
1. 没有指定正确的MIME类型
2. 文件对象没有正确关闭
3. 没有验证文件格式和大小

## 修复方案

### 方案1：修复文件上传格式（推荐）

```python
def upload_image_to_wechat(self, image_path):
    """上传图片到企业微信获取media_id"""
    try:
        # 检查文件是否存在
        if not os.path.exists(image_path):
            logging.error(f"图片文件不存在: {image_path}")
            return None
            
        # 检查文件大小
        file_size = os.path.getsize(image_path)
        if file_size > 2 * 1024 * 1024:  # 2MB
            logging.error(f"图片文件过大: {file_size} bytes，超过2MB限制")
            return None
            
        # 检查文件格式
        file_extension = os.path.splitext(image_path)[1].lower()
        if file_extension not in ['.jpg', '.jpeg', '.png']:
            logging.error(f"不支持的图片格式: {file_extension}")
            return None
            
        # 确定MIME类型
        mime_type = 'image/jpeg' if file_extension in ['.jpg', '.jpeg'] else 'image/png'
        
        # 构建上传URL
        upload_url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/upload_media?key={self.webhook_url.split('=')[1]}&type=image"
        
        # 使用with语句确保文件正确关闭
        with open(image_path, 'rb') as file_obj:
            files = {
                'media': (os.path.basename(image_path), file_obj, mime_type)
            }
            
            upload_response = requests.post(
                upload_url, 
                files=files, 
                timeout=10,
                proxies=None  # 禁用代理
            )
            
        if upload_response.status_code == 200:
            upload_result = upload_response.json()
            if upload_result.get('errcode') == 0:
                media_id = upload_result.get('media_id')
                logging.info(f"图片上传成功，获取到media_id: {media_id}")
                return media_id
            else:
                logging.error(f"图片上传失败: {upload_result}")
                return None
        else:
            logging.error(f"图片上传HTTP请求失败: {upload_response.status_code}")
            return None
            
    except Exception as e:
        logging.error(f"上传图片时出错: {e}")
        return None
```

### 方案2：使用base64方式上传（备选）

企业微信也支持base64方式上传图片：

```python
def upload_image_base64(self, image_path):
    """使用base64方式上传图片"""
    try:
        # 检查文件大小和格式
        if not self._validate_image_file(image_path):
            return None
            
        # 读取图片并转换为base64
        with open(image_path, 'rb') as f:
            image_data = f.read()
            
        base64_data = base64.b64encode(image_data).decode('utf-8')
        md5_hash = hashlib.md5(image_data).hexdigest()
        
        # 构建请求
        upload_url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/upload_media?key={self.webhook_url.split('=')[1]}&type=image"
        
        data = {
            'media': base64_data,
            'md5': md5_hash
        }
        
        response = requests.post(
            upload_url,
            json=data,
            timeout=10,
            proxies=None
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('errcode') == 0:
                return result.get('media_id')
            else:
                logging.error(f"base64图片上传失败: {result}")
        else:
            logging.error(f"base64图片上传HTTP失败: {response.status_code}")
            
        return None
        
    except Exception as e:
        logging.error(f"base64上传图片时出错: {e}")
        return None
```

### 方案3：图片格式转换

如果当前图片格式有问题，可以转换为标准格式：

```python
def convert_image_to_standard_format(self, image_path):
    """转换图片为标准格式"""
    try:
        from PIL import Image
        
        # 打开图片
        with Image.open(image_path) as img:
            # 转换为RGB模式（如果是RGBA）
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # 保存为JPEG格式
            new_path = image_path.rsplit('.', 1)[0] + '_converted.jpg'
            img.save(new_path, 'JPEG', quality=85)
            
            logging.info(f"图片已转换为标准格式: {new_path}")
            return new_path
            
    except Exception as e:
        logging.error(f"图片格式转换失败: {e}")
        return image_path
```

## 修改main.py中的send_to_wechat方法

```python
def send_to_wechat(self, report_data):
    """发送报表到企业微信群，只发送图片"""
    if not report_data:
        logging.warning("没有报表数据可发送")
        return False

    try:
        # 检查是否有图片报表
        if 'image_filename' in report_data:
            logging.info("检测到图片报表，准备发送图片")
            image_path = os.path.join(self.file_dir, report_data['image_filename'])
            
            # 尝试使用JPEG格式的图片（如果存在）
            jpeg_path = image_path[:-4] + '.jpg' if image_path.endswith('.png') else image_path

            # 优先使用JPEG格式
            if os.path.exists(jpeg_path):
                image_path = jpeg_path
                logging.info(f"使用JPEG格式图片: {image_path}")
            elif not os.path.exists(image_path):
                logging.warning(f"图片文件不存在: {image_path}")
                return False
            else:
                logging.info(f"使用PNG格式图片: {image_path}")

            if os.path.exists(image_path):
                # 检查文件格式
                file_extension = os.path.splitext(image_path)[1].lower()
                if file_extension not in ['.jpg', '.jpeg', '.png']:
                    logging.error(f"不支持的图片格式: {file_extension}")
                    return False
                else:
                    # 使用修复后的上传方法
                    logging.info("上传图片获取media_id...")
                    media_id = self.upload_image_to_wechat(image_path)
                    
                    if media_id:
                        # 创建图片消息
                        image_message = {
                            "msgtype": "image",
                            "image": {
                                "media_id": media_id
                            }
                        }

                        logging.info("发送图片消息...")
                        response = requests.post(
                            self.webhook_url,
                            json=image_message,
                            timeout=10,
                            proxies=None
                        )

                        if response.status_code == 200:
                            result = response.json()
                            if result.get('errcode') == 0:
                                logging.info("图片报表发送成功")
                                return True
                            else:
                                logging.error(f"图片发送失败: {result}")
                                return False
                        else:
                            logging.error(f"图片HTTP请求失败: {response.status_code}")
                            return False
                    else:
                        logging.error("图片上传失败，无法获取media_id")
                        return False
            else:
                logging.warning("没有找到图片文件")
                return False
        else:
            logging.warning("没有图片报表")
            return False

    except Exception as e:
        logging.error(f"发送报表时出错: {e}")
        return False
```

## 验证步骤

1. **检查图片文件**：确认图片格式为PNG或JPG，大小不超过2MB
2. **测试上传**：使用修复后的上传方法测试
3. **检查响应**：确认返回正确的media_id
4. **验证发送**：确认图片消息能正常发送

## 预期结果
- 消除"invalid media type"错误
- 图片上传成功率接近100%
- 支持PNG和JPG格式的图片文件