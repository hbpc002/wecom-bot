#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 app.js 文件中的 sendToWecom 函数
"""

import os
import shutil
from datetime import datetime

# 文件路径
APP_JS_PATH = r'd:\Documents\G-ide\wecom-bot\static\js\app.js'

# 备份文件
backup_path = APP_JS_PATH + f'.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}'
shutil.copy2(APP_JS_PATH, backup_path)
print(f"✓ 已备份原文件到: {backup_path}")

# 完整的正确的 app.js 内容
CORRECT_APP_JS = r"""// 全局变量
let selectedFiles = [];

// DOM元素
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const selectBtn = document.getElementById('selectBtn');
const fileList = document.getElementById('fileList');
const fileItems = document.getElementById('fileItems');
const uploadBtn = document.getElementById('uploadBtn');
const clearBtn = document.getElementById('clearBtn');
const uploadProgress = document.getElementById('uploadProgress');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const uploadResults = document.getElementById('uploadResults');
const resultsContent = document.getElementById('resultsContent');

// 标签页切换
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tabName = btn.dataset.tab;

        // 更新按钮状态
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        // 更新内容显示
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${tabName}Tab`).classList.add('active');
    });
});

// 拖拽上传功能
dropZone.addEventListener('click', () => {
    fileInput.click();
});

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-over');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');

    const files = Array.from(e.dataTransfer.files).filter(file =>
        file.name.toLowerCase().endsWith('.zip')
    );

    if (files.length > 0) {
        addFiles(files);
    } else {
        alert('请选择 .zip 格式的文件');
    }
});

selectBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    fileInput.click();
});

fileInput.addEventListener('change', (e) => {
    const files = Array.from(e.target.files);
    if (files.length > 0) {
        addFiles(files);
    }
    fileInput.value = ''; // 清空input以允许重复选择同一文件
});

// 添加文件到列表
function addFiles(files) {
    selectedFiles = [...selectedFiles, ...files];
    updateFileList();
    fileList.style.display = 'block';
}

// 更新文件列表显示
function updateFileList() {
    fileItems.innerHTML = '';

    selectedFiles.forEach((file, index) => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.innerHTML = `
            <div class="file-info">
                <div class="file-name">${file.name}</div>
                <div class="file-size">${formatFileSize(file.size)}</div>
            </div>
            <button class="file-remove" onclick="removeFile(${index})">删除</button>
        `;
        fileItems.appendChild(fileItem);
    });

    if (selectedFiles.length === 0) {
        fileList.style.display = 'none';
    }
}

// 删除文件
function removeFile(index) {
    selectedFiles.splice(index, 1);
    updateFileList();
}

// 清空文件列表
clearBtn.addEventListener('click', () => {
    selectedFiles = [];
    updateFileList();
});

// 上传文件
uploadBtn.addEventListener('click', async () => {
    if (selectedFiles.length === 0) {
        alert('请先选择文件');
        return;
    }

    // 显示进度条
    uploadProgress.style.display = 'block';
    uploadResults.style.display = 'none';
    uploadBtn.disabled = true;

    const formData = new FormData();
    selectedFiles.forEach(file => {
        formData.append('files[]', file);
    });

    try {
        const xhr = new XMLHttpRequest();

        // 监听上传进度
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percent = Math.round((e.loaded / e.total) * 100);
                progressFill.style.width = percent + '%';
                progressText.textContent = percent + '%';
            }
        });

        // 监听完成
        xhr.addEventListener('load', () => {
            if (xhr.status === 200) {
                const response = JSON.parse(xhr.responseText);
                displayResults(response);
                selectedFiles = [];
                updateFileList();
                refreshFilesList();
            } else {
                alert('上传失败：' + xhr.statusText);
            }
            uploadBtn.disabled = false;
        });

        // 监听错误
        xhr.addEventListener('error', () => {
            alert('上传失败，请检查网络连接');
            uploadBtn.disabled = false;
        });

        xhr.open('POST', '/api/upload');
        xhr.send(formData);

    } catch (error) {
        console.error('上传错误:', error);
        alert('上传失败：' + error.message);
        uploadBtn.disabled = false;
    }
});

// 显示上传结果
function displayResults(response) {
    uploadProgress.style.display = 'none';
    uploadResults.style.display = 'block';

    resultsContent.innerHTML = `
        <div class="result-summary">
            <h4>${response.message}</h4>
        </div>
    `;

    if (response.results) {
        response.results.forEach(result => {
            const resultItem = document.createElement('div');
            resultItem.className = `result-item ${result.success ? '' : 'error'}`;
            resultItem.innerHTML = `
                <div class="result-filename">${result.filename}</div>
                <div class="result-message">${result.message}</div>
                ${result.data ? `
                    <div class="result-data">
                        日期: ${result.data.date} | 
                        总次数: ${result.data.total_operations} | 
                        参与人数: ${result.data.people}
                    </div>
                ` : ''}
            `;
            resultsContent.appendChild(resultItem);
        });
    }
}

// 查询日报表
document.getElementById('queryDailyBtn').addEventListener('click', async () => {
    const dateInput = document.getElementById('dailyDate');
    const date = dateInput.value;

    if (!date) {
        alert('请选择日期');
        return;
    }

    try {
        const response = await fetch(`/api/reports/daily/${date}`);
        const data = await response.json();

        if (data.success) {
            displayDailyReport(data);
        } else {
            document.getElementById('dailyReport').innerHTML = `
                <div class="empty-state">${data.message || '没有找到数据'}</div>
            `;
        }
    } catch (error) {
        console.error('查询失败:', error);
        alert('查询失败：' + error.message);
    }
});

// 显示日报表
function displayDailyReport(data) {
    const reportDiv = document.getElementById('dailyReport');

    let html = `
        <div class="report-summary">
            <h3>📊 ${data.date} 统计报表</h3>
            <div class="summary-grid">
                <div class="summary-item">
                    <div class="summary-label">总听录音次数</div>
                    <div class="summary-value">${data.total_operations}</div>
                </div>
                <div class="summary-item">
                    <div class="summary-label">参与人数</div>
                    <div class="summary-value">${data.people_count}</div>
                </div>
                <div class="summary-item">
                    <div class="summary-label">平均每人次数</div>
                    <div class="summary-value">${(data.total_operations / data.people_count).toFixed(1)}</div>
                </div>
            </div>
        </div>
        
        <table class="data-table">
            <thead>
                <tr>
                    <th>排名</th>
                    <th>团队</th>
                    <th>姓名</th>
                    <th>账号</th>
                    <th>当日听录音次数</th>
                    <th>月累计</th>
                </tr>
            </thead>
            <tbody>
    `;

    data.data.forEach((item, index) => {
        html += `
            <tr>
                <td>${index + 1}</td>
                <td>${item.team}</td>
                <td>${item.name}</td>
                <td>${item.account}</td>
                <td>${item.daily_count}</td>
                <td><strong>${item.monthly_count}</strong></td>
            </tr>
        `;
    });

    html += `
            </tbody>
        </table>
    `;

    reportDiv.innerHTML = html;
}

// 查询月报表
document.getElementById('queryMonthlyBtn').addEventListener('click', async () => {
    const monthInput = document.getElementById('monthlyDate');
    const month = monthInput.value;

    if (!month) {
        alert('请选择月份');
        return;
    }

    try {
        const response = await fetch(`/api/reports/monthly/${month}`);
        const data = await response.json();

        if (data.success) {
            displayMonthlyReport(data);
        } else {
            document.getElementById('monthlyReport').innerHTML = `
                <div class="empty-state">${data.message || '没有找到数据'}</div>
            `;
        }
    } catch (error) {
        console.error('查询失败:', error);
        alert('查询失败：' + error.message);
    }
});

// 显示月报表
function displayMonthlyReport(data) {
    const reportDiv = document.getElementById('monthlyReport');

    let html = `
        <div class="report-summary">
            <h3>📊 ${data.year_month} 月度统计报表</h3>
            <div class="summary-grid">
                <div class="summary-item">
                    <div class="summary-label">总听录音次数</div>
                    <div class="summary-value">${data.total_operations}</div>
                </div>
                <div class="summary-item">
                    <div class="summary-label">参与人数</div>
                    <div class="summary-value">${data.people_count}</div>
                </div>
                <div class="summary-item">
                    <div class="summary-label">平均每人次数</div>
                    <div class="summary-value">${(data.total_operations / data.people_count).toFixed(1)}</div>
                </div>
            </div>
        </div>
        
        <table class="data-table">
            <thead>
                <tr>
                    <th>排名</th>
                    <th>团队</th>
                    <th>姓名</th>
                    <th>账号</th>
                    <th>月累计次数</th>
                </tr>
            </thead>
            <tbody>
    `;

    data.data.forEach((item, index) => {
        html += `
            <tr>
                <td>${index + 1}</td>
                <td>${item.team}</td>
                <td>${item.name}</td>
                <td>${item.account}</td>
                <td><strong>${item.total_count}</strong></td>
            </tr>
        `;
    });

    html += `
            </tbody>
        </table>
    `;

    reportDiv.innerHTML = html;
}

// 刷新文件列表
document.getElementById('refreshFilesBtn').addEventListener('click', refreshFilesList);

async function refreshFilesList() {
    const filesTable = document.getElementById('filesTable');
    filesTable.innerHTML = '<p class="loading">加载中...</p>';

    try {
        const response = await fetch('/api/files');
        const data = await response.json();

        if (data.success && data.files.length > 0) {
            let html = `
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>文件名</th>
                            <th>大小</th>
                            <th>修改时间</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            data.files.forEach(file => {
                html += `
                    <tr>
                        <td>${file.filename}</td>
                        <td>${formatFileSize(file.size)}</td>
                        <td>${file.modified}</td>
                        <td>
                            <button class="btn btn-danger btn-sm" onclick="deleteUploadedFile('${file.filename}')">删除</button>
                        </td>
                    </tr>
                `;
            });

            html += `
                    </tbody>
                </table>
            `;

            filesTable.innerHTML = html;
        } else {
            filesTable.innerHTML = '<div class="empty-state">暂无已上传文件</div>';
        }
    } catch (error) {
        console.error('获取文件列表失败:', error);
        filesTable.innerHTML = '<div class="empty-state">加载失败</div>';
    }
}

// 删除已上传的文件
async function deleteUploadedFile(filename) {
    if (!confirm(`确定要删除文件 "${filename}" 吗？\n\n注意：删除后无法恢复！`)) {
        return;
    }

    try {
        const response = await fetch(`/api/files/${encodeURIComponent(filename)}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            alert(data.message || '文件删除成功');
            // 刷新文件列表
            refreshFilesList();
        } else {
            alert('删除失败：' + (data.error || '未知错误'));
        }
    } catch (error) {
        console.error('删除文件失败:', error);
        alert('删除失败：' + error.message);
    }
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// 发送到企业微信 - 测试环境
document.getElementById('sendTestBtn').addEventListener('click', async () => {
    await sendToWecom('test');
});

// 发送到企业微信 - 生产环境
document.getElementById('sendProdBtn').addEventListener('click', async () => {
    await sendToWecom('prod');
});

async function sendToWecom(env) {
    const dateInput = document.getElementById('wecomDate');
    const date = dateInput.value;

    if (!date) {
        alert('❌ 请先选择日期');
        return;
    }

    const envName = env === 'test' ? '测试环境' : '生产环境';
    
    // 开始前确认(生产环境)
    if (env === 'prod') {
        const confirmed = confirm(
            `⚠️ 确认发送到生产环境？\n\n` +
            `📅 日期: ${date}\n` +
            `🎯 环境: ${envName}\n\n` +
            `点击【确定】发送，点击【取消】放弃发送`
        );
        
        if (!confirmed) {
            console.log('❌ 用户取消了发送到生产环境');
            alert('ℹ️ 已取消发送操作');
            return;
        }
        console.log('✅ 用户确认发送到生产环境');
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
        alert(`❌ 发送失败：${error.message}\n\n请检查网络连接或查看控制台了解详情`);
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
        console.log('发送操作结束');
    }
}

// 保存定时任务设置
document.getElementById('saveScheduleBtn').addEventListener('click', async () => {
    const enabled = document.getElementById('scheduleEnabled').checked;
    const time = document.getElementById('scheduleTime').value;

    try {
        const response = await fetch('/api/schedule/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ enabled, time })
        });

        const data = await response.json();

        if (data.success) {
            alert('定时任务设置已保存');
        } else {
            alert('保存失败：' + data.error);
        }
    } catch (error) {
        console.error('保存失败:', error);
        alert('保存失败：' + error.message);
    }
});

// 加载定时任务状态
async function loadScheduleStatus() {
    try {
        const response = await fetch('/api/schedule/status');
        const data = await response.json();

        if (data.success) {
            document.getElementById('scheduleEnabled').checked = data.enabled;
            document.getElementById('scheduleTime').value = data.time;
        }
    } catch (error) {
        console.error('加载定时任务状态失败:', error);
    }
}

// 设置默认日期为今天
document.getElementById('dailyDate').valueAsDate = new Date();
document.getElementById('wecomDate').valueAsDate = new Date();
const today = new Date();
document.getElementById('monthlyDate').value = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}`;

// 页面加载时刷新文件列表和定时任务状态
window.addEventListener('load', () => {
    refreshFilesList();
    loadScheduleStatus();
});
"""

# 写入正确的内容
with open(APP_JS_PATH, 'w', encoding='utf-8') as f:
    f.write(CORRECT_APP_JS)

print(f"✓ 已修复 app.js 文件")
print(f"\n主要修改:")
print("  1. 恢复了完整的 sendToWecom 函数")
print("  2. 优化了生产环境发送确认对话框")
print("  3. 添加了更清晰的提示信息")
print("\n说明:")
print("  - 测试环境：直接发送，无需确认")
print("  - 生产环境：需要点击【确定】才会发送")
print("  - 如果点击【取消】，会显示'已取消发送操作'提示")
