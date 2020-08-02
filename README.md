# Utaufile

#### 介绍
操作UTAU ust文件和袅袅虚拟歌手nn文件的python库

本python库依赖[numpy](https://numpy.org/) 

#### 安装
> pip install utaufile

#### 功能

##### ust文件：
- 解析与写入ust文件
- 导出nn文件
- 导出mid文件（需要[mido](https://mido.readthedocs.io/en/latest/index.html)）
- 导出dv文件（需要[dvfile](https://gitee.com/oxygendioxide/dvfile)）
- 导出五线谱（需要[music21](http://web.mit.edu/music21/doc/index.html)）
- 批量获取、替换、设置歌词
- flag解析
- 获取音域
- 量化（将音符对齐到节拍线）

##### nn文件：
- 解析与写入nn文件
- 导出ust文件
- 导出mid文件（需要[mido](https://mido.readthedocs.io/en/latest/index.html)）
- 导出dv文件（需要[dvfile](https://gitee.com/oxygendioxide/dvfile)）
- 导出五线谱（需要[music21](http://web.mit.edu/music21/doc/index.html)）

#### 参与贡献

1.  Fork 本仓库
2.  新建 Feat_xxx 分支
3.  提交代码
4.  新建 Pull Request