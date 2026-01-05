#!/bin/bash

# Py Copilot 图标生成脚本
# 用于生成各种尺寸的图标文件

echo "正在生成 Py Copilot 应用图标..."

# 创建图标目录（如果不存在）
mkdir -p icons

# 使用在线服务或工具生成图标
# 这里我们创建一个简单的SVG图标

cat > icons/icon.svg << 'EOF'
<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
  <defs>
    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#4A90E2;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#357ABD;stop-opacity:1" />
    </linearGradient>
    <linearGradient id="grad2" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#FFD700;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#FFA500;stop-opacity:1" />
    </linearGradient>
  </defs>
  
  <!-- 背景圆形 -->
  <circle cx="256" cy="256" r="240" fill="url(#grad1)" stroke="#2C5AA0" stroke-width="8"/>
  
  <!-- Python 蛇形设计 -->
  <g transform="translate(256,256)">
    <!-- 蛇身 -->
    <path d="M -80 -40 C -80 -80, -40 -100, 0 -80 C 40 -60, 60 -20, 40 0 C 20 20, -20 20, -40 0 C -60 -20, -60 -40, -80 -40 Z" 
          fill="url(#grad2)" stroke="#FF8C00" stroke-width="2"/>
    
    <!-- 蛇头 -->
    <ellipse cx="20" cy="-20" rx="25" ry="20" fill="url(#grad2)" stroke="#FF8C00" stroke-width="2"/>
    
    <!-- 眼睛 -->
    <circle cx="10" cy="-25" r="3" fill="#000"/>
    <circle cx="25" cy="-25" r="3" fill="#000"/>
    
    <!-- 舌头 -->
    <path d="M 35 -20 L 45 -18 L 35 -16 Z" fill="#FF0000"/>
    
    <!-- 代码符号装饰 -->
    <text x="-20" y="30" font-family="Arial, sans-serif" font-size="16" font-weight="bold" fill="#2C5AA0">AI</text>
  </g>
  
  <!-- 装饰性元素 -->
  <circle cx="120" cy="120" r="8" fill="#FFD700" opacity="0.8"/>
  <circle cx="392" cy="120" r="6" fill="#FFD700" opacity="0.6"/>
  <circle cx="120" cy="392" r="6" fill="#FFD700" opacity="0.6"/>
  <circle cx="392" cy="392" r="8" fill="#FFD700" opacity="0.8"/>
  
  <!-- 底部装饰线 -->
  <rect x="100" y="440" width="312" height="4" fill="#FFD700" opacity="0.7" rx="2"/>
</svg>
EOF

# 转换 SVG 为不同格式
# 注意：这里需要安装 imagemagick 或类似的工具
# 如果没有安装，则创建占位文件

# 生成 PNG 图标（需要 imagemagick）
if command -v convert >/dev/null 2>&1; then
    echo "使用 ImageMagick 生成 PNG 图标..."
    convert icons/icon.svg -resize 16x16 icons/tray-icon.png
    convert icons/icon.svg -resize 32x32 icons/app-icon-32.png
    convert icons/icon.svg -resize 64x64 icons/app-icon-64.png
    convert icons/icon.svg -resize 128x128 icons/app-icon-128.png
    convert icons/icon.svg -resize 256x256 icons/app-icon-256.png
    convert icons/icon.svg -resize 512x512 icons/app-icon-512.png
    
    # 生成 ICO 文件（Windows）
    convert icons/icon.svg -resize 256x256 icons/icon.ico
    
    # 生成 ICNS 文件（macOS）
    if command -v iconutil >/dev/null 2>&1; then
        mkdir -p icons/app-icon.iconset
        convert icons/icon.svg -resize 16x16 icons/app-icon.iconset/icon_16x16.png
        convert icons/icon.svg -resize 32x32 icons/app-icon.iconset/icon_16x16@2x.png
        convert icons/icon.svg -resize 32x32 icons/app-icon.iconset/icon_32x32.png
        convert icons/icon.svg -resize 64x64 icons/app-icon.iconset/icon_32x32@2x.png
        convert icons/icon.svg -resize 128x128 icons/app-icon.iconset/icon_128x128.png
        convert icons/icon.svg -resize 256x256 icons/app-icon.iconset/icon_128x128@2x.png
        convert icons/icon.svg -resize 256x256 icons/app-icon.iconset/icon_256x256.png
        convert icons/icon.svg -resize 512x512 icons/app-icon.iconset/icon_256x256@2x.png
        convert icons/icon.svg -resize 512x512 icons/app-icon.iconset/icon_512x512.png
        
        iconutil -c icons icons/app-icon.iconset
        rm -rf icons/app-icon.iconset
        
        mv icons/icon.icns icons/app-icon.icns 2>/dev/null || true
    fi
else
    echo "ImageMagick 未安装，创建占位图标文件..."
    
    # 创建占位文件
    touch icons/tray-icon.png
    touch icons/app-icon-16.png
    touch icons/app-icon-32.png
    touch icons/app-icon-64.png
    touch icons/app-icon-128.png
    touch icons/app-icon-256.png
    touch icons/app-icon-512.png
    touch icons/icon.ico
    touch icons/app-icon.icns
    
    echo "注意：请手动安装 ImageMagick 或手动创建图标文件"
    echo "SVG 源文件已创建在 icons/icon.svg"
fi

echo "图标生成完成！"
echo "请根据需要调整图标文件"