# 洛克乐器演奏 — 下个对话交接日志

更新日期：2026-10-15（UTC）
用途：新对话请先读取本文件和当前 `main` 源码，再继续修改；不要从旧版源码归档或旧对话的补丁片段重新开始。

## 1. 仓库和最新已验证版本

- GitHub 仓库：<https://github.com/tryq123333/->
- 默认分支：`main`
- Android 源码归档（仓库根目录）：`LuokeAutoPiano.zip`
- 当前归档 blob SHA：`b238a04416a2d55028ee6014e9b66311e3698990`
- 自动构建工作流：<https://github.com/tryq123333/-/blob/main/.github/workflows/build-apk.yml>
- 最近一次已成功构建：Run #68
  <https://github.com/tryq123333/-/actions/runs/38666732178>
- Run #68 对应提交：`8564dc517df51855145e7649a0f5b65516cfa231`
- 工作流最后同步源码后的主分支 HEAD：`6d0cf51cf6615084ef8419e87644a71f644e7d79`（`Sync seekable music overlay source [skip ci]`）
- Run #68 已确认成功：Android `assembleDebug`、`testDebugUnitTest`、APK 上传、源码 ZIP 打包/上传、源码同步回主分支均为 success。
- Run #68 构建产物：`LuokeAutoPiano-debug-apk`（artifact ID `11942190748`）和 `LuokeAutoPiano-source-zip`（artifact ID `11941311672`）。从上述 Actions 页面打开 Artifacts 即可下载。

重要：构建成功与 JVM 单元测试通过并不等于已经在用户手机上完成真机测试。请不要宣称已在手机里实测，除非之后真的做了。

## 2. 项目是什么

这是给《洛克王国：世界》游戏内九键乐器使用的 Android 自动演奏工具。用户主要在 Android 手机上操作，编程经验有限，倾向于让助手直接检查源码、完成修改、跑 GitHub Actions，再提供可直接用的 APK 和 ZIP。

当前 app 的用户可见名称已改为“洛克乐器演奏”；桌面图标为音乐符号矢量图。源码目录在归档解压后为 `LuokeAutoPiano/`，语言为 Java，使用 Gradle；工作流在 Ubuntu 上配置 JDK 17、Android platform/build-tools 35，然后编译和跑 JVM 测试。

## 3. 当前已实现并在 Run #68 构建验证的功能

### 悬浮控制窗与校准
- 初始悬浮音乐图标默认位于屏幕左上方。
- 收起时应回到单独的音乐图标，不显示曲名/时间状态条；点图标可展开控制面板。
- 默认九键布局在完成键位校准前，展开面板只显示校准和图标/收起入口相关控件；校准后恢复完整控制功能。
- 控制面板可以拖动/缩放，内容会根据宽度自动换行。用户偏好默认一行，缩窄后分行；不要再单独添加冗余的“收起”按钮，图标本身用于收起/展开。
- 九键键位 A/D、J/K/L 的默认布局和手机触控适配是项目历史需求；如果修改按键或校准逻辑，应检查是否回归。

### 音符滚动悬浮窗
- 默认紧凑、透明背景，允许移动、缩放；行数随尺寸变化。
- 横向拖动谱面可以实际 seek 到播放进度；底部独立进度条可用于定位。过去出现过“拖一下直接跳到结尾”和拖动窗口抖动，后续修改需特别回归测试。
- 曲名/当前时间在谱面顶部，与音符区域处在同一横向布局；用户希望音符经过播放竖线后渐淡，并且音符能在曲名/时间文字的后面经过，而不是被一块矩形空白区域硬裁掉。
- 播放竖线保留但要低对比度；横向音符轨道底纹应隐藏或与透明背景融合，避免出现层层框线感。
- 每个音块应能看出音名，不应因音块偏窄就完全不显示音名。
- 谱面里的播放/暂停、“A/B循环”和“×”控件底色/边框要淡；底部进度轨道、选中范围和当前进度指示同样要低对比度。最近改动把进度轨道颜色降到 alpha `0x1c` 左右，选中范围约 alpha `0x2b`，当前指示约 alpha `0x75`。

### A/B 循环
- 名称统一为“A/B循环”，不再叫“片段”。
- 从主悬浮控制面板打开 A/B 设置界面；界面有启用状态、A 起点秒数、B 终点秒数、把当前位置设为 A/B 的入口和“重置 A/B”按钮。
- 滚动音符界面上的 “A/B循环” 按钮保持当前交互：轻点启用/关闭，长按可进入起止点编辑。不要把谱面上的启用/关闭功能改成另一个用途。
- 已修正核心范围逻辑：A/B 开启时，播放有效范围为 A 到 B；A/B 关闭时，有效范围恢复整首歌的 0 到总时长，但保留已保存的 A/B 点，以便下次重新开启循环。
- “重置 A/B”应把 A 恢复为 0，把 B 恢复为整首歌时长（例如歌曲 30 秒时 A=0、B=30），并更新持久化值与设置框显示。
- 变更运行中的播放范围会停止旧播放 worker，让新的范围在下一次开始时生效；真机测试时需确认行为清楚、不会卡住。

### 音符渐淡、应用身份、导入音乐
- 最近的品牌/谱面脚本已移除挡住标题/时间区域的 note exclusion clip，因此音符可以从文字后方经过；绘制代码应继续让标题/控制绘制在音符之上，保持文字可读。
- 底部播放进度条在最近一轮再次变淡。
- app_name 资源是“洛克乐器演奏”；Manifest 的 `icon` 和 `roundIcon` 指向 `@drawable/ic_music_note`，对应矢量资源 `app/src/main/res/drawable/ic_music_note.xml`。
- 已移除 App 里跳转到 <https://rocomusic.cn/> 的独立入口/功能；MIDI 文件选择仍然需要 Android 的 `android.net.Uri` 导入，不能为了去掉站点入口而误删文件导入需要的 Uri。
- 支持导入 MIDI，并在悬浮窗中切换已导入曲目。

## 4. 最新请求的状态

截至 Run #68，下面这些工作已经进入构建流程且构建成功：
1. 音符经过播放线后渐淡，并允许在曲名/时间绘制层后方经过。
2. 底部进度条及当前范围/位置提示进一步变淡。
3. A/B 关闭时实际播放范围回到整首歌。
4. A/B 设置页增加“重置 A/B”。
5. 用户可见应用名改为“洛克乐器演奏”，启动器图标改为音乐符号。

这些项目目前属于“代码已应用、构建和 JVM 测试通过、待用户手机实测”，不要把真机验证说成已经完成。

## 5. 自动构建工作流的注意事项

工作流会执行以下流程：
1. 从根目录解压 `LuokeAutoPiano.zip`；
2. 依次应用一系列历史兼容/布局步骤；
3. 特别重要的近期逻辑脚本：
   - `.github/scripts/apply_ab_loop_range_logic_v3.py`
   - `.github/scripts/apply_ab_loop_branding_v3.py`
4. 执行 `./gradlew --no-daemon assembleDebug`；
5. 执行 `./gradlew --no-daemon testDebugUnitTest`；
6. 上传 APK 和源码 ZIP；
7. 把优化后的 `LuokeAutoPiano.zip` 同步回 `main`。

修改之前一定要先检查当前 `LuokeAutoPiano.zip`、`.github/workflows/build-apk.yml` 和上述脚本。工作流里的脚本有 marker/idempotent 检查，源码归档和脚本都可能影响最终产物；不要只改一处便假设 APK 已包含修改。以前出现过补丁编码/截断、锚点匹配失败、漏导入 `Uri`、重复 `showSegmentDialog()` 等问题，所以一定要让工作流真实执行并看日志。
如果只改了交接日志，注意它本身在仓库根目录，不属于 `LuokeAutoPiano/`，不会被打包进源码 ZIP。

## 6. 下个对话建议的首要步骤

1. 先阅读本文件，再打开最新 Run #68 检查页面和主分支源 ZIP。
2. 不要重复实现已经进入 Run #68 的 A/B 重置、A/B 关闭后整曲播放、音符穿过标题/时间渐淡、进度条变淡和品牌图标修改。
3. 优先请用户在手机上实测最新 APK，然后收集具体症状/截图/日志；根据实际结果定位。
4. 如果出现新问题，直接对着当前源码改、运行构建测试，避免靠猜测或只改 UI 截图。
5. 交付给用户时使用干净、直观的文件名；提供实际存在且刚刚确认的 APK/源码链接。不要把中间补丁或说明 TXT 放进用户的源码 ZIP，也不要声称没有执行过的测试。

本日志是下一对话的上下文交接，不替代源码与最新 Actions 日志；若任何描述和当前 `main` 实际内容不一致，以最新源码与成功构建日志为准。

## 7. 2026-10-15 演奏开关、回起点与轻滑跳跃修正

- 本轮 patch marker：`NOTE_ROLL_PLAY_REWIND_SEEK_GUARD_V1`。
- 工作流调用脚本：`.github/scripts/apply_note_roll_play_controls_and_seek_guard_v1.py`，位于应用既有的 `apply_ab_loop_branding_v3.py` 后面；脚本已做成可重复应用，不能假设 ZIP 一定是旧的未打补丁源码。
- 最新自动同步源码提交：`eaf064ff9e91afaef0cb824ec2b8d542af753b97`；当前主分支 `LuokeAutoPiano.zip` blob SHA：`e7c4cd94182966bbdf6b0dc3cc62d509bdf25b6e`。该自动同步步骤在工作流的 APK 构建、JVM 测试、APK/源码产物上传之后执行，因此该轮工作流已走到末尾同步阶段。仍未做 Android 真机验证。
- 音符悬浮窗的“开始/暂停/继续”合并为一个“演奏”控件：静止/暂停时灰色普通态，播放中绿色高亮；点击使用既有的启动/暂停/继续逻辑。悬浮窗内也提供 `⏮︎` 回起点入口。
- 主控制面板旧“停止”按钮更名为 `⏮︎`，不再终止线程：A/B 循环启用时定位到保存的 A 点；A/B 关闭时定位整首歌 0 秒。谱面游标、绝对 seek、轻滑 seek 的活动范围也改为根据 A/B 是否启用选择 A–B 或整首歌；A/B 关闭时仍可保留并显示已保存的标记点。
- 轻滑问题修正：底部精确进度轨道不再在 `ACTION_DOWN` 时立即跳位；轻点会在抬手时定位，拖动则必须先越过水平触摸阈值。音符区域相对滑动改为更温和的增量，每次手势位移最多 500 ms 且不超过可视时间窗的 6%。窗口移动/缩放改用欧氏距离 `Math.hypot(dx, dy)` 判断是否越过触摸阈值，阈值之前不更新窗口布局，避免斜向轻微手抖触发抖动。
- 新增 `NoteRollGestureMath.java` 与 `NoteRollGestureMathTest.java`，覆盖轻滑增量上限和绝对定位手势阈值。当前已完成本地静态检查、XML 解析和手势数学辅助类检查；本地环境无法联网下载 Gradle，正式 Android 构建由 GitHub Actions 执行。
- 视频记录位于私有仓库 `tryq123333/chat` 的 `VID_20261015_102652_1.mp4`。本次连接能确认文件和提交，但无法通过 GitHub 文件接口读取/播放二进制视频，因此没有声称看过视频具体帧；本轮针对源码中可复现的触控路径修正。后续若用户手机上仍能复现，请直接上传视频到对话，或提供帧截图/操作位置，继续校准手势门槛。

## 8. 2026-10-15 本轮谱面/曲目/A-B 窗口修正

- 脚本：`.github/scripts/apply_song_specific_roll_ui_v2.py`，工作流在旧触控保护脚本后调用；当前主分支源归档 blob SHA：`ab4ef2a0069a2b012c4f99d2af243d93f186af06`，同步提交：`0ed56e00dc82e82439b55c2e63098ae9f84a3c53`。
- 构建 Run #80 成功（`f9dea6d3b8e4965953005c7a2af63d2040e3f0b9`）：APK 编译、JVM 单元测试、APK 上传、源码 ZIP 打包/上传、源码同步均为 success。APK artifact ID：`11947340451`；source ZIP artifact ID：`11947775135`。构建不代表完成 Android 真机测试。
- 音符谱面改为单一“演奏”按钮，播放时高亮；谱面打开时隐藏主控制面板重复的“开始/暂停/继续”，关闭谱面时恢复。校准完成后，悬浮控制面板不再显示校准入口；需要重新校准时可先重置/更改乐器布局，再重新打开面板。
- 谱面按键标记按用户提供的游戏截图绘制为九键手碟图标，88 键钢琴模式保留音名；渐变白色播放线移到 `⏮︎` 右侧附近。
- 播放中开始滑动谱面/进度轨道时，先暂时暂停音符调度，在松手定位后无提示音地恢复演奏，避免播放时持续刷新和手势 seek 互相争抢造成跳进度。
- A/B 设置卡改为默认更小的可滚动窗口，可拖动标题移动、拖动右下角改大小，并保存窗口位置/尺寸。右上角改成明确的 `×`，关闭无需先验证输入；有效的“完成”仍会保存设置。外部触摸也可关闭窗口。
- 曲目列表为每首 MIDI 展示独立的移调值与音域检查结果，并提供 -12 到 +12 半音的独立滑杆。各曲目的移调按文件路径单独保存；重新选择曲目时恢复上次值，同时更新主界面移调滑杆与谱面显示。
- 后续真机测试优先检查：打开谱面后主面板是否不再重复显示开始/暂停；九键图标是否与游戏按键形状/顺序匹配；播放中滑动是否平稳且松手后从目标位置继续；A/B 卡的关闭与大小调整；两首歌分别移调后切换再返回，移调是否分别保留。若游戏内图标的实际音高顺序与当前近似绘制映射不同，应按真机截图调整 `NoteRollView.drawGameKeyIcon` 中图标顺序，不改 MIDI 播放音高映射。

## 9. 2026-10-15 再次合并演奏按钮、改用截图原图标及进一步淡化

- 工作流新增步骤与脚本：`.github/scripts/apply_roll_single_control_icons_fade_v3.py`（在 `apply_song_specific_roll_ui_v2.py` 之后、Gradle 编译之前执行）。脚本会在打包时生成 `app/src/main/res/drawable-nodpi/note_key_atlas.webp`；该图集来自用户提供的游戏截图裁切，网格中的实际顺序与 `InstrumentLayout.PITCHES` 对应：A2、E3、F3、G3、A3、B3、C4、D4、E4。
- 本轮构建 Run #82 成功：<https://github.com/tryq123333/-/actions/runs/38679710333>。APK 构建、JVM 测试、APK 和源码 ZIP 上传、源码 ZIP 同步均成功。APK artifact ID：`11946988093`；source ZIP artifact ID：`11946863280`。当前根目录源码 ZIP blob SHA：`01129628dd2934e9a50ee5a479c8e1fe7e57fb03`。
- “演奏”统一：音符谱面顶部只有一个固定文字为“演奏”的按钮；播放中高亮，暂停/未播放时回到普通态，点击根据当前状态执行开始、暂停或继续。主悬浮控制面板也从“开始”+“暂停/继续”两颗按钮改成一颗“演奏”，播放时高亮；谱面打开时主面板此按钮隐藏，关闭谱面后重新显示。
- 音符图标不再使用代码画的近似符号，改为从用户截图裁切的游戏原按键图，按 MIDI 音高映射索引缩小画在每个音块中。钢琴 88 键模式继续显示传统音名。
- 谱面播放白线 alpha 从 `0x66` 降至 `0x26`，线宽降至 `0.85dp`；曲名文字 alpha 从不透明改为 `0x99`，时间文字 alpha 为 `0x88`。
- 后续修正提交 `6b6e51383884af8d3efd6be9417c8e2ce93ed21e` 只给 v3 脚本的 marker append 加了存在性判断，避免之后每次构建都重复追加注释标记；不改变该 APK 的运行逻辑。
- APK 与打包后 ZIP 已做容器完整性检查，并确认 APK 中含有 `res/drawable-nodpi-v4/note_key_atlas.webp`。本轮尚未在用户手机上真机测试；重点验证谱面和主面板都只显示一颗“演奏”、九个音块的图标对应是否准确、白线/曲名是否足够淡，以及开始/暂停点击行为。

## 10. 2026-10-15 谱面滑动、按键图标边缘、A/B 缩小和停止后画面稳定

- 构建修正版本：Run #89，提交 `1d67bfa9119356fa7edbb2fb28c5ac3e5990d74b`。APK 编译、JVM 单元测试、APK 上传、源码 ZIP 打包/上传、源码同步步骤均已 success；APK artifact ID `11948807127`，source ZIP artifact ID `11948861972`。根目录 `LuokeAutoPiano.zip` 当前 blob SHA `87e95b5695e276caa09d9743c6ad66a6d8d78206`。APK 从该构建 artifact 解出并用 ZIP 完整性检查确认可读取；含 `res/drawable-nodpi-v4/note_key_atlas.webp`。仍需手机真机回归。
- 最新脚本：`.github/scripts/apply_roll_seek_icon_stability_v4.py`，在 V3 原图标/演奏按钮脚本之后执行。
- 谱面打开时隐藏主悬浮面板中的“谱面”和 `⏮︎` 两个按钮，关闭谱面后恢复显示。
- 触摸底部进度条的 `ACTION_DOWN` 立即暂时暂停播放调度；真正的定位仍在水平拖动越过阈值或手指抬起时完成，随后恢复之前正在播放的曲目，减少播放中滑动与后台时钟更新竞态造成的跳位。播放循环排队的 UI 帧在暂停/停止/滑动冻结期间不再覆盖用户选中的位置。
- 原游戏按键图标改为只绘制每个 64x64 图块中间的内圈图像，并以椭圆裁切，去除原图的青色/粉色外层按键底板；图标最大尺寸缩小为 13dp，并且音块进入屏幕右侧时，只有音块本身宽度足够显示图标才绘制图标，避免图形先于有色方块出现。
- A/B 设置卡默认宽度最大 310dp、高度最大 245dp，内边距、标题、勾选框、输入框、按钮和右下角调整把手同步缩小；仍保留拖动移动、调整大小、滚动和关闭功能。
- 停止或自然结束时，不再把谱面游标强行跳到 A/B 末端；丢弃在停止/暂停后排队的旧游标帧，保持最后显示的音符时间窗，避免停止后可视音符突然换一批。
- 为使后续构建可重复，工作流旧版游标白线检查现同时接受旧色和已淡化后的 `0x26ffffff`；逐曲目 UI 脚本的图标 postcondition 兼容原图标渲染函数；V3 图标脚本在检测到图集初始化已存在时不再重复写入 `final gameKeyAtlas`，避免再次编译失败。
- 本轮发现并修复了两次编译问题：游标回调在错误作用域引用 `playbackWorker`，以及图集初始化在不完整源码标记下重复插入。Run #89 的最终 Java 编译和 JVM 单元测试已通过。

## 11. 2026-10-15 按最新九键参考图重做图集、图标先框后图、修正桌面名称和图标配色

- 最终成功构建 Run #95：<https://github.com/tryq123333/-/actions/runs/38685092172>。构建、JVM 单元测试、APK 上传、源码 ZIP 打包/上传以及 ZIP 同步均 success。APK artifact ID `11949473875`，source ZIP artifact ID `11949179006`。主分支 `LuokeAutoPiano.zip` blob SHA `87bdf0bcf2b2c07c8880cd9a1e5fc20e2b00b686`；源码同步提交 `7583e4f575234346f5430d643c4748d6f24cf1ff`。
- 用户最新九键参考图生成的新图集为 `app/src/main/res/drawable-nodpi/note_key_atlas.webp`，最终是 96x96、RGBA、每格 32px；9 个完整奶白圆形按 T/Y/U、F/G/H/J/K、B 的视觉顺序排列并去除了截图里的琴键字母/深色背景。NoteRollView 使用 32px 单元格的完整图标，不再放大只截中间符号，保持完整圆边和 glyph 比例。
- 新入场效果：先绘制滚动音符的彩色圆角矩形块，只有在音符方块已从右边进入并有足够可见宽度后，图标才在 5dp 行程内渐显；防止按键图片先于外围方框出现。
- `AndroidManifest.xml` 的 application label 从硬编码的“洛克自动琴”改为 `@string/app_name`，`strings.xml` 正式名称是“洛克乐器演奏”；service label 保持单独的“洛克自动琴触控服务”。
- `drawable/ic_music_note.xml` 已反转颜色：背景（旧绿色区域）为白色，原白色音乐符号为黑色；launcher 的 `icon` 和 `roundIcon` 继续引用该向量资源。
- 新脚本：`.github/scripts/apply_roll_reference_icon_and_app_identity_v5.py`，在 v4 触控/窗口脚本之后、Gradle 编译之前执行。修正了 V3 脚本重复构建时的兼容检查，使其能够接受已经存在的原图渲染及合并“演奏”按钮/新增控制面板状态刷新，不再强行要求旧手绘图或旧视图布局。
- 已检查最终 source ZIP 可完整解压，并核对上述 manifest、strings、icon、图集大小、NoteRollView 完整图标 crop 及 frame-first 渐显逻辑。APK ZIP 完整性也通过检查。未完成 Android 真机测试；后续优先让用户确认图标实际大小/映射、方块先显图标后显的动画、桌面名称和白底黑音符图标是否按预期显示。

## 12. 2026-10-15 隐藏谱面内回起点、左移音符入场、滑动游标代数与强制刷新桌面标识

- 最终成功构建 Run #98：<https://github.com/tryq123333/-/actions/runs/38687196134>；APK 编译、JVM 单元测试、APK 上传、源 ZIP 上传及同步全部 success。APK artifact ID `11949823469`，source ZIP artifact ID `11950187969`。根目录源码 ZIP blob SHA：`122c705a50694227fe94818114d1f00601ab2d5f`。APK 已从本次成功构建的 artifact 重新抽出并核对 ZIP 完整性；本次版本为 versionCode 2、versionName 0.2.0，不能再混用 Run #95 的旧安装包。
- 新脚本：`.github/scripts/apply_roll_final_controls_seek_launcher_v6.py`，在 V5 图标/身份修正之后执行。
- NoteRollView 顶部已移除自身的 `⏮︎` 按钮，仅保留关闭和统一“演奏”按钮，并将“演奏”的命中区域扩为原来的右侧空位。主悬浮控制面板里的“谱面”和 `⏮︎` 仍由 V4 按 noteRollView 状态隐藏/恢复。
- 新增 `NoteRollGestureMath.pastEntranceBuffer` 与 JVM 测试：音符左边缘至少进入可见画布 24dp 后才参与绘制，给有色音符方块和完整键图保留显示空间，避免图标从窗口最右侧抢先出现。
- 新增 `playbackUiGeneration`：拖动开始、定位提交和抬手结束都递增代数；播放线程排队的游标帧带有代数快照，仅当代数仍匹配且未暂停/停止时才更新 UI。这样即使旧帧在抬手恢复后才执行，也不能把播放位置覆回旧进度。
- 为确保用户设备实际获得新桌面元数据，`AndroidManifest.xml` 改为使用新资源 `@string/launcher_app_name`、`@drawable/launcher_luoke_v2`（`icon` 与 `roundIcon`），新图标 XML 内容为白底黑音符；同时把 versionCode 从 1 提至 2、versionName 改为 0.2.0，以避开旧安装包/桌面缓存混淆。
- 用户说的新视频在私有仓库当前路径为 `VID_20261015_132056.mp4`（约 11.6 MB）。GitHub 连接能读到该文件存在，但二进制 blob 无法解码为可预览帧；旧路径 `VID_20261015_102652_1.mp4` 已删除。因此这轮没有声称看过视频画面，轻滑问题按已确认的播放线程/UI 帧竞态修正。若需要针对具体帧/手势轨迹做进一步定位，请让用户直接将 MP4 上传到对话。
- 后续真机验证：更新安装 versionCode 2 的 APK后，确认应用桌面名称/图标更新；打开谱面时确认主面板及谱面头部都没有 `⏮︎`，关闭谱面后主面板的按钮恢复；播放中在底部进度条轻滑、抬手后确认不回跳旧帧；确认音符方块在距右边缘 24dp 后出现且内部键图不抢先。

## 13. 2026-10-15 恢复滚动音符窗口回起点并放到 A/B 右侧

- 成功构建 Run #102：<https://github.com/tryq123333/-/actions/runs/38688366740>。APK build、JVM tests、APK artifact 上传和源码 ZIP 打包/上传已通过；APK artifact ID `11950004639`。APK 从 artifact 解压并通过 ZIP 完整性检查。
- 新脚本：`.github/scripts/apply_roll_rewind_next_to_ab_v7.py`，在 V6 最终 UI 脚本之后执行。滚动音符窗口恢复 `⏮︎`，放在第二行 `A/B循环` 控件右边，位置紧挨；对应 touch hitbox 为 x=69..97dp、y=50..72dp，并调用既有 `onRewind()`，行为仍遵循 AB 开启回 A、关闭回曲目起点。
- 为保证旧补丁链可以重复运行，V1 的 postcondition 不再强制要求回起点符号必须出现在 NoteRollView 的旧头部；V4 允许继续使用 V6 的 `playbackUiGeneration` 游标帧保护，不会试图覆盖成更弱的旧实现。
- APP versionCode 提升至 3，versionName `0.3.0`。此版本应覆盖前一版 0.2.0。
- 尚未做真机 UI 回归；安装后确认滚动谱面内 A/B 右侧能看到 `⏮︎` 并且可以点按，同时初始浮窗的对应按钮在谱面打开时仍保持隐藏。

## 14. 2026-10-15 曲目列表实时搜索

- 成功构建 Run #105：<https://github.com/tryq123333/-/actions/runs/38701893207>。APK 编译、JVM 单元测试、APK artifact 上传、源码 ZIP 打包/上传以及源码同步全部 success。APK artifact ID `11957075007`，source ZIP artifact ID `11955979852`。
- 新脚本：`.github/scripts/apply_song_picker_live_search_v1.py`，在 A/B 右侧回起点的 V7 补丁之后执行；版本号升至 versionCode 4、versionName `0.4.0`。
- 曲目弹窗标题和说明下新增“搜索已导入的歌曲名”输入框，按输入内容实时过滤 songCard 标签中的歌名（忽略大小写、支持部分匹配）；没有匹配歌曲时显示“没有找到匹配的曲目”。筛选只控制卡片的 View.VISIBLE/GONE，不删曲目、不改变各曲目单独保存的移调值，也不改当前选曲。
- 为支持真正输入，曲目弹窗 WindowManager LayoutParams 移除了 `FLAG_NOT_FOCUSABLE`，加入键盘调整模式；搜索框可触摸聚焦。其余列表点击选曲、音域检查和各歌独立移调控件保持不变。
- APK artifact 已解压并运行 ZIP 完整性检查；本地交付路径为 `/mnt/data/LuokeAutoPiano.apk`，文件大小 87,454 字节。尚未手机真机验证搜索框键盘显示和匹配体验。

## 15. 2026-10-15 批量导入 MIDI 曲目

- 构建 Run #107：<https://github.com/tryq123333/-/actions/runs/38702800244>。新批量导入补丁执行成功，Android APK 编译、JVM 单元测试、APK 上传、源码 ZIP 打包/上传及源码同步步骤全部 success。APK artifact ID `11957151337`，source ZIP artifact ID `11957056538`。
- 新补丁脚本 `.github/scripts/apply_batch_midi_import_v1.py`，在实时搜索脚本之后执行；应用版本提高至 versionCode 5 / versionName `0.5.0`。
- 主界面的导入按钮现在显示“2. 批量导入 MIDI 曲谱（支持多选）”。文档选择器使用 `Intent.EXTRA_ALLOW_MULTIPLE`，兼容 ClipData 多选与原来的单文件 data URI。
- 每个 URI 分别复制到私有 `files/imported_songs`、验证 MIDI 是否能解析、限制单文件 32 MB；无效文件只清理该文件，不影响同批其他曲目。每首歌各自保存显示名与独立移调初值。
- 导入一首歌时沿用原行为：立即选中它。批量导入时如已有有效当前选曲则保留当前选曲；如尚无有效选曲，则自动选中第一首成功导入的曲目。导入结束显示成功/失败数量，可从曲目列表及搜索框管理新增曲目。
- 当前轮交付 APK 已从构建产物解出为 `/mnt/data/LuokeAutoPiano.apk`，大小 88,842 字节，ZIP 完整性检查通过且包含 classes.dex 与 resources.arsc。JVM 单元测试通过；尚未在实体 Android 设备上验证不同文件选择器支持多选的具体 UI 行为。

## 16. 2026-10-15 滚动谱面调速与曲目移除

- 成功构建 Run #109：<https://github.com/tryq123333/-/actions/runs/38707584238>。APK 编译、JVM 单元测试、APK 上传、源码 ZIP 打包/上传和源码同步均 success。APK artifact ID `11958759189`，source ZIP artifact ID `11958509813`。APK 已下载到 `/mnt/data/LuokeAutoPiano.apk`，92,158 字节，ZIP 完整性检查通过；versionCode `6` / versionName `0.6.0`。
- 新脚本：`.github/scripts/apply_roll_speed_and_song_removal_v1.py`，在批量导入脚本之后执行。
- NoteRollView 在 A/B 循环和 `⏮︎` 下一行增加紧凑的速度滑杆，范围 50%–200%，每 5% 一档，实时显示百分比。轻触或拖动轨道后松手应用设置；设置保存到现有 `MainActivity.KEY_SPEED`，下次打开主界面也能看到。
- 演奏中更改速度时，service 根据当前速度和播放时间重算当前 MIDI 游标，递增 seek 版本并通知播放线程，让它从当前位置重新计算后续音符的等待时间，而不是强行停止/重启整首曲目。
- 曲目列表每首歌标题行右侧新增 `移除` 按钮。操作有二次确认，删除的仅是应用私有曲库中的导入副本（包括旧版 current_song.mid 条目），不会删除下载目录原件。同步清理该曲目的显示标签和独立移调偏好；若移除的是当前选曲，会先停止播放、清空当前引用和移调/AB 状态，并关闭谱面浮窗，避免继续引用被删文件。
- 仍需手机真机验证：小窗口下滑杆能否易于操作、播放中调速后是否流畅衔接；在曲目列表移除非当前曲目、当前曲目以及最后一首曲目时，确认删除确认框、曲目列表和谱面状态都正常。

## 17. 2026-10-16 修正主悬浮控制小窗随播放/暂停状态调整尺寸

- 用户通过两张截图明确指出：问题是左下方“音乐图标展开后的初始主控制悬浮窗”，不是滚动音符谱面窗口。播放/暂停及谱面开关导致内部可见控件变化时，主控制窗的外层尺寸/底板没有跟着变化。
- 修正已合入工作流 `.github/workflows/build-apk.yml`，提交 `607103e775378519620dd5bbb5f733189ec10610`。修复步骤 `Auto-size the expanded music control panel on state changes` 在构建时修改 `MusicAccessibilityService.java`，使用 `syncControlPanelHeightToContent()` 在主面板内容状态变化时重设 `controlParams.height = WRAP_CONTENT`，并在调整后把窗口纵向位置限制在屏幕内。对旧版保存的固定面板高度做一次迁移清理，保留宽度、移动与手动调整能力。
- 明确撤掉了错误尝试的 NoteRoll/滚动谱面高度适配：最终源码不再含 `syncNoteRollWindowToPlaybackState`、`noteRollBaseHeightPx` 或 `playbackOverlayHeight()`；滚动谱面仍独立显示/关闭，不与主控制窗收起/展开联动。曲目列表滚动位置恢复逻辑也保留。
- 为避免源码归档已经应用补丁时重复运行导致失败，工作流中的 V3–V7 音符补丁、曲目实时搜索、批量导入、速度/移除、曲目滚动位置等步骤均增加已应用标记检测，已存在时跳过而不是重复打补丁。
- 成功构建 Run #117：https://github.com/tryq123333/-/actions/runs/38829183394，提交 `607103e775378519620dd5bbb5f733189ec10610`。APK Build、JVM tests、APK 上传、源码 ZIP 打包/上传、源码同步全部 success。APK artifact ID `12016107249`；source ZIP artifact ID `12016491816`。应用版本 `versionCode 9` / `versionName 0.9.0`。APK 已保存到 `/mnt/data/LuokeAutoPiano.apk`，大小 93,794 字节，ZIP 完整性检查通过；确认包含 `classes.dex`、`resources.arsc` 和 `note_key_atlas`。
- 仍未做 Android 真机 UI 回归。手机上优先打开主音乐图标的小窗，分别检查未播放→播放、播放→暂停、谱面打开/关闭几种状态下，底板高度是否紧贴当前可见按钮/内容、没有多余空白或裁切；确认滚动谱面能独立开关且高度保持用户设定。若边框仍未跟随某个特定状态，需按该状态再检查状态刷新函数是否被调用，不要改成固定 124/148dp 的谱面高度逻辑。
## 18. 2026-10-16 A/B设置窗响应式缩放、谱面细边、速度透明度、进度时间与历史改动审计

- 用户本轮要求：A/B循环设置窗口拖动改变大小时内部控件/文字需一起缩放；滚动谱面窗口透明外框增加一圈很淡的边界；速度滑杆降低饱和度和不透明度；底部进度条下方显示当前/总时长，时间标签随播放游标水平移动；检查此前变更有没有遗漏。
- 新构建脚本 `.github/scripts/apply_ab_dialog_responsive_roll_polish_v1.py`，并在 workflow 里新增 `Make A/B dialog responsive and polish note-roll visuals; audit preserved features` 步骤。A/B窗口按当前外框尺寸相对基准计算横/纵比例，递归缩放内部控件尺寸、边距、内边距与字号；拖动窗口位置逻辑和储存尺寸仍保留。
- NoteRollView 外框增添 `0x339bb1c1` / `0.8dp` 低对比描边；底部进度轨移到时间标签上方，时间标签显示 `当前位置 / 歌曲总时长`，采用小号淡色字体并随进度游标水平移动。速度标题、轨道、填充和滑块颜色只在 `drawSpeedControl()` 区域内降对比度，未改变播放速度算法及控制范围。
- 审计时发现一个真实遗漏：`launcher_luoke_v2.xml` 资源早已是白底黑音符，但 `AndroidManifest.xml` 仍引用旧 `@drawable/ic_music_note`（绿底白符），所以安装包桌面图标继续显示旧配色。当前脚本已将 manifest 的 `icon` 和 `roundIcon` 改回 `@drawable/launcher_luoke_v2`，并将旧 `ic_music_note.xml` 也统一为白底黑符。应用名称仍使用 `@string/launcher_app_name`（洛克乐器演奏）。
- 构建前 feature audit 已通过并验证这些历史功能标记/关键入口仍存在：主面板按状态重新测量高度、谱面独立开关、原游戏按键图集、合并演奏按钮、进度 seek 代数保护、A/B/回起点、每曲目移调/音域检查、实时搜索、曲目列表滚动还原、批量 MIDI 导入、速度调节/移除曲目。没有再引入谱面与主面板联动，也没有使用先前错误的播放态固定谱面高度。
- Run #120 成功：https://github.com/tryq123333/-/actions/runs/38832553412。构建前审计、Android APK 编译、JVM 单元测试、APK 与源码 ZIP 上传、源码同步全部 success。代码提交 `e68ed5c72cf788e3883a889b13c7bd50183e09bb`，源码同步提交 `68af310e004076f3817281274529c9add223578e`。APK artifact ID `12017891410`，source ZIP artifact ID `12017846425`。版本 `versionCode 10` / `versionName 1.0.0`。APK 已核验 ZIP 完整性，路径 `/mnt/data/LuokeAutoPiano.apk`，95,874 bytes，SHA-256 `710ebfc9c20578994626ab6b4894fd5e2afddb2bc23f13bed03d6c20bda7d305`。
- 仍需用户真机回归：缩小/放大 A/B 设置窗时按钮和字号是否恰当、软键盘弹出期间内容是否仍可滚动/可点；谱面外框是否足够淡但可辨；播放、暂停与拖动时底部时间是否同步；速度滑杆是否视觉柔和；更新安装后确认桌面图标确实白底黑音符（若系统仍显示缓存旧图标，先检查安装包版本 1.0.0 是否覆盖成功）。本构建通过编译/单测，但尚未由 Android 真机截图确认最终视觉效果。
## 19. 2026-10-16 入场音符渐现、应用改名奏乐、隐藏 88 键入口与修复 A/B 完成按钮

- 用户要求：播放期间滚动谱面的音符入场增加渐现（与越过游标后渐淡相反）；应用及应用内标题统一改为“奏乐”；暂时移除 88 键钢琴选项并改说明；修复 A/B 设置填入 A 点后点“完成”无响应；继续缩小 A/B 窗口内容。
- 新脚本 `.github/scripts/apply_songle_fade_name_abfix_v2.py`，构建工作流在上轮的 A/B/谱面视觉修正后运行。NoteRollView 在播放中使用单独的淡入进度，与现有游标后渐淡 alpha 相乘；`NoteRollGestureMath.enteringNoteFadeIn()` 新增 JVM 回归测试，覆盖 0%、50%、100% 端点。
- A/B 的“完成/重置”按钮从 ScrollView 的可滚动输入内容移到卡片固定底栏，以免被滚动区域或键盘遮挡；点击“当前位置设为 A/B”后自动收起数字键盘，点“完成”也先收起键盘；缩放改为用 WeakHashMap 保存尺寸基线，不覆盖 `View.setTag()` 的公共 tag 槽。缩放比例按窗口 LayoutParams 实际宽高计算，不会因键盘触发的布局变化突然改变字号/控件尺寸。对话框默认 250dp × 185dp 左右、尺寸上限约 270dp × 210dp（受屏幕限制），标题/输入框/按钮字号及高度同步缩小；仍可拖动/缩放。
- 主界面标题、桌面名、应用名、无障碍服务标签和说明中的品牌名改为“奏乐”。主界面取消乐器模式下拉框，改成固定“当前乐器：九键手碟”；删除 88 键模式说明、校准标签及音域检查描述。`InstrumentLayout.selectedMode()` 将旧偏好迁移到九键模式，防止已选过 88 键的旧安装升级后仍然走 88 键路径；底层历史算法保留但当前不可选。
- 保留并在构建前审计：白底黑音符桌面图标引用、原游戏九键图集、合并“演奏”按钮、A/B/回起点与 seek 代数保护、曲目独立移调/音域检查、实时搜索、曲目滚动位置恢复、批量导入、速度调节/移除曲目、主控制窗随内容重测高度、谱面独立开关。本轮未重新引入谱面与主控制窗联动。
- 成功构建 Run #122：https://github.com/tryq123333/-/actions/runs/38842157848，代码提交 `c94fc0dae313d704ef97795395010da370d9784e`，源码同步提交 `9f90ad637f4e0e1ba35e27b05004988b2c6dd434`。APK 编译、JVM tests、上传 APK 与 source ZIP、源码同步均 success。APK artifact ID `12021836066`，source ZIP artifact ID `12021845989`。版本 `versionCode 11` / `versionName 1.1.0`。APK `/mnt/data/LuokeAutoPiano.apk` 为 95,546 bytes，SHA-256 `7d724d55880efde045b8b6c63e788053dbbce9f66a16471abfe7e97b9f07fa16`；源码 `/mnt/data/LuokeAutoPiano.zip` 为 105,022 bytes，SHA-256 `104474a05b790fa1c2b813a0d560db7384ef21342ec5fe7214f745c649494710`。两个 artifact 和最终 APK ZIP 完整性检查通过。
- 仍需要真机检查：音符从右侧出现时渐现是否够自然；A/B 设点后按钮是否可点且完成后确实保存；小尺寸窗口是否仍能读清 A/B 数字/滚动输入区；桌面与应用内名字是否都显示“奏乐”；主界面不再出现 88 键选项。Actions/单元测试通过并不代表已在手机实测。
## 20. 2026-10-16 A/B 设置首屏按钮、实时循环同步和紧凑比例修正

- 用户实测 1.1.0 后再次反馈 A/B 不能使用：首次打开设置看不到“当前位置设为 A/B”，必须在空白区的滚动区域中往下滑；设置勾选框与谱面 A/B 状态不同步；整体卡片/按钮宽度占比依然太大。
- 根据截图与源码确认根因：`setButtons` 与 A/B 输入字段同在 `bodyScroll` 里，但滚动区高度使用剩余空间权重，标题、底部“重置/完成”与调整大小提示压缩了输入区，使设点按钮落到首屏之外。版本 V3 将 `bodyScroll` 固定为约 70dp（只负责勾选框与输入字段），A/B 设点按钮移到它外面且固定可见；“重置 A/B/完成”改为 wrap-content 宽度、居中显示，避免每颗按钮强行铺满半个窗。标题、输入框、行高、间距和外框默认尺寸再缩小；默认约 225dp × 185dp，限制最大尺寸，首次迁移时清理之前保存的过大宽高，但保留窗口位置。
- 增加 `applyAbLoopEnabledFromDialog(boolean)` 并给复选框添加 `OnCheckedChangeListener`：用户勾选/取消时立即写入开关状态、重新计算活动范围并更新 `NoteRollView.setAbLoopEnabled`；如果正在暂停中的播放线程仍持有旧的播放范围，会请求停止旧线程，下一次开始使用新范围。点击“完成”仍会保存输入框里的 A/B 时间并做范围合法性检查。
- 新脚本 `.github/scripts/apply_ab_loop_dialog_sync_compact_v3.py`，工作流中步骤 `Fix A/B dialog visibility, compact controls and sync loop state`。修正前还修复了补丁链的一个历史非幂等阻塞：当源码已经含有渐淡/品牌标记时跳过旧版 `apply_ab_loop_branding_v3.py`，并让上一版 feature-audit 接受当前 5 参数的 A/B 缩放函数与 `奏乐` 应用名。
- 成功构建 Run #127：https://github.com/tryq123333/-/actions/runs/38844963430，提交 `a68eb4a5262d90cfbdae8fffefed479bfd2b32f3`。构建前审计、Android APK 编译、JVM tests、APK/source ZIP 上传与源码同步全部 success。APK artifact ID `12022773958`，source ZIP artifact ID `12023120633`。版本 `versionCode 12` / `versionName 1.2.0`。交付 APK `/mnt/data/LuokeAutoPiano.apk`（96,458 bytes，SHA-256 `12384610a6bfc8e509ec48a3cb6651c8d1e5f5f6ad581108edf1e9c0762728e8`），源码 `/mnt/data/LuokeAutoPiano.zip`（105,492 bytes，SHA-256 `451cd88ebeee7cba96a4b977155b9a0a7715ba5ec532d49b8673692d14cafa3c`），两个文件均已跑 ZIP 完整性检查。
- 真机回归优先确认：打开 A/B 窗后无需滚动就能看到 A/B 输入、两颗设点按钮、重置和完成；设 A 后按完成会保存/关闭，输入非法 A/B 时有明确提示且不关闭；勾选 A/B 时谱面显示/开关状态即时同步；按钮按文字收缩且卡片整体更小。不应改动谱面独立开关或此前的九键映射、渐现、奏乐命名、白底黑音符图标等既有功能。
