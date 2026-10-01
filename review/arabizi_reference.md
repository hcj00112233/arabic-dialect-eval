# Arabizi（Franco-Arabic）映射规则调研

> 用途：评测 T7 模块 case 设计 + 作品集附录。Arabizi = Arabi + Englizi，90 年代末因键盘/手机不支持阿语字符而自发演化，至今仍是 MENA 年轻人聊天、社媒、客服 DM 的真实输入形态。

## 一、核心设计原理

1. **视觉镜像**：数字长得像旋转/镜像后的阿语字母——`3` 是反写的 `ع`，`7` 像 `ح`，`6` 像 `ط`
2. **加点规则**： apostrophe `'` 表示"给字母加点"——`3`=`ع` → `3'`=`غ`（ع 加点）；`7`=`ح` → `7'`=`خ`（ح 加点）；`9`=`ص` → `9'`=`ض`
3. **音值替代**：拉丁字母按发音对应（sh=ش, th=ث, gh=غ, kh=خ, dh=ذ, aa=ا, ee=ي, oo=و）
4. **地域音系映射**（关键信息差）：数字映射的对象是**该方言区对这个字母的实际发音**，而非字母本身——这是埃及 ق→2 的由来（埃及方言中 ق 发作声门塞音 /ʔ/，等于 hamza 的音）

## 二、核心映射表（英语系 Arabizi，埃及/海湾/黎凡特通用基线）

| 数字 | 阿语字母 | 音 | 例词 | 设计逻辑 |
|---|---|---|---|---|
| 2 | ء | 声门塞音 /ʔ/ | so2al = سؤال | 形似；**埃及/黎凡特兼表 ق**（因方言中 ق 发作 /ʔ/） |
| 3 | ع | 咽音 /ʕ/ | 3arabi = عربي | 3 是 ع 的镜像 |
| 3' | غ | /ɣ/ | 3'aleeb = غريب | 3 加点 = ع 加点 |
| 4 | ش（部分地区） | /ʃ/ | 4abab = شباب（较少见，多用 sh） | 地区性用法，埃及偶见 |
| 5 | خ | /x/ | 5abar = خبر | 形似（部分约定） |
| 6 | ط |  emphatic /tˤ/ | 6aalib = طالب | 6 像 ط |
| 6' | ظ | emphatic /ðˤ/ | 6'alam = ظلام（较少见） | 6 加点 |
| 7 | ح | 清咽擦音 /ħ/ | 7abibi = حبيبي | 7 像 ح |
| 7' / 5 | خ | /x/ | 7'bar / 5bar = خبر | 7 加点；5 为另一支约定，**خ 的写法是埃及/海湾差异点之一** |
| 8 | ق 或 غ | /q/ 或 /ɣ/ | 8albi = قلبي（海湾/黎凡特部分地区） | 8 像带两点的 ق；**埃及几乎不用 8**（埃及 ق→2） |
| 9 | ص | emphatic /sˤ/ | 9abr = صبر（埃及基线约定之一） | 9 像 ص 的变体 |

## 三、地域差异（评测的核心陷阱区）

| 现象 | 埃及 | 海湾 | 黎凡特 | 马格里布（北非法语系） |
|---|---|---|---|---|
| ق | **2**（发 /ʔ/） | 8 / q / g（部分词发 /g/：gahwa=قهوة） | 2（城市口音发作 /ʔ/） | **9** |
| ج | g（geem 发硬 g：gamel=جمل） | j | j | j / dj |
| خ | 5 或 7' | 5 或 kh | 5 或 7' | kh |
| غ | 3' | 3' 或 gh | 3' | gh |
| ش | sh / ch / 4（少） | sh | sh / ch | **ch**（法语 ch=/ʃ/） |
| 长元音 u | oo | oo | oo | **ou**（法语正字法） |
| ث | s / th | th | s / t | t / th |

**马格里布 Arabizi 是完全另一套体系**：底层是法语不是英语，`ch`=`ش`、`ou`=`و`、`9`=`ق`、`3`=`ع`。同一个字符串 `ch9ara` 在马格里布=شقارة，在埃及约定下无法解析。用户已声明不测摩洛哥方言，但**评测报告里应注明此边界，并指出马格里布 Arabizi 是未来扩展方向**——这本身就是专业性的体现。

## 四、歧义与难点（为什么这是模型的硬骨头）

1. **数字歧义**：`3ndy 3 talabat` = عندي ٣ طلبات（"我有3个订单"）——同一个 `3` 既是字母又是真数字，只能靠上下文消歧
2. **无空格标准**：`wla` = ولا，`w la` 另有所指；连写/分写无约定
3. **元音完全自由**：`kteer / ktiir / keter` 都=كتير，同一词一人一个写法
4. **英阿混排**：真实输入是 `ana busy دلوقتي` 这种三语混合（Arabizi + English + 阿语字符同句）
5. **检测本身就是难题**：`ana 3ayez booking` 先判"这是 Arabizi 还是乱码/英语"，再判方言区（gamel 的 g → 埃及），再解析

## 五、对评测/数据工作的意义

- **检测层**：模型能否识别输入是 Arabizi（而非英语乱码）——客服/社交场景的前置能力
- **理解层**：解析语义 + 判断方言区（通过 g/j、2/8/9 的用法反推用户是埃及人还是海湾人）
- **生成层**：能否用 Arabizi 回复（营销/客服场景的真实需求）
- **数据层**：Arabizi 语料几乎全是 UGC（评论/DM/推文），爬取可得但**清洗极难**（无标准拼写、无法用常规阿语 NLP 工具分词）——这正是"低资源数据工程"的典型问题

## 六、评测 case 设计方向（T7 模块）

| case 类型 | 示例 | 测什么 |
|---|---|---|
| 基础解析 | `3ayez a7giz tazkara le Riyadh bokra` → 转阿语并回答 | 映射表掌握 |
| 数字歧义 | `3ndy 3 so2al` | 上下文消歧 |
| 方言区识别 | `gamel awi` vs `jameel marra` | g/j 反推埃及 vs 海湾 |
| 混排理解 | `mumkin أشوف الـ menu?` | 三语混合输入 |
| 生成 | "用 Arabizi 回复这个埃及客户的投诉" | 生成能力+地域适配 |
| 陷阱题 | 埃及约定下含 `8` 的句子 | 模型是否知道埃及不用 8 |

## 参考来源

- [LearnType: Arabizi Numbers Explained](https://learntype.app/blog/arabizi-numbers-explained-2-3-5-6-7-9-and-the-arabic-sounds-they-represent)
- [The Arabic Keyboard: Franco Arabic](https://www.thearabickeyboard.com/franco-arabic-typing/)
- [KALIMAH Center: Arabizi & Franco Arabic](https://kalimah-center.com/arabic-letters-in-numbers/)
- [Talkpal: Mastering Arabizi](https://talkpal.ai/mastering-arabizi-the-ultimate-guide-to-writing-arabic-in-latin-script/)
- [ReplAi: Franco-Arabic, How AI Understands 3arabi Text](https://www.replai.now/blog/franco-arabic-arabizi-how-ai-understands-3arabi-text)
- [Omlyar: Beginner's Guide to Arabizi（地区差异）](https://www.omlyar.com/blog/arabizi-guide)
