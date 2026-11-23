-- 《字里寻踪》按字分表。重复导入时保留已有记录。
SET NAMES utf8mb4;
USE zili_xunzong;

CREATE TABLE IF NOT EXISTS cultural_men (
  id VARCHAR(32) PRIMARY KEY,
  hanzi VARCHAR(8) NOT NULL,
  region VARCHAR(16) NOT NULL,
  place VARCHAR(120) NOT NULL,
  title VARCHAR(200) NOT NULL,
  body TEXT NOT NULL,
  source_title VARCHAR(255) NOT NULL,
  source_section VARCHAR(160) NOT NULL,
  source_url VARCHAR(900) NOT NULL,
  verification_status VARCHAR(32) NOT NULL,
  material_use VARCHAR(160) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS cultural_cha (
  id VARCHAR(32) PRIMARY KEY,
  hanzi VARCHAR(8) NOT NULL,
  region VARCHAR(16) NOT NULL,
  place VARCHAR(120) NOT NULL,
  title VARCHAR(200) NOT NULL,
  body TEXT NOT NULL,
  source_title VARCHAR(255) NOT NULL,
  source_section VARCHAR(160) NOT NULL,
  source_url VARCHAR(900) NOT NULL,
  verification_status VARCHAR(32) NOT NULL,
  material_use VARCHAR(160) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS cultural_chuan (
  id VARCHAR(32) PRIMARY KEY,
  hanzi VARCHAR(8) NOT NULL,
  region VARCHAR(16) NOT NULL,
  place VARCHAR(120) NOT NULL,
  title VARCHAR(200) NOT NULL,
  body TEXT NOT NULL,
  source_title VARCHAR(255) NOT NULL,
  source_section VARCHAR(160) NOT NULL,
  source_url VARCHAR(900) NOT NULL,
  verification_status VARCHAR(32) NOT NULL,
  material_use VARCHAR(160) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS cultural_deng (
  id VARCHAR(32) PRIMARY KEY,
  hanzi VARCHAR(8) NOT NULL,
  region VARCHAR(16) NOT NULL,
  place VARCHAR(120) NOT NULL,
  title VARCHAR(200) NOT NULL,
  body TEXT NOT NULL,
  source_title VARCHAR(255) NOT NULL,
  source_section VARCHAR(160) NOT NULL,
  source_url VARCHAR(900) NOT NULL,
  verification_status VARCHAR(32) NOT NULL,
  material_use VARCHAR(160) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS cultural_yuan (
  id VARCHAR(32) PRIMARY KEY,
  hanzi VARCHAR(8) NOT NULL,
  region VARCHAR(16) NOT NULL,
  place VARCHAR(120) NOT NULL,
  title VARCHAR(200) NOT NULL,
  body TEXT NOT NULL,
  source_title VARCHAR(255) NOT NULL,
  source_section VARCHAR(160) NOT NULL,
  source_url VARCHAR(900) NOT NULL,
  verification_status VARCHAR(32) NOT NULL,
  material_use VARCHAR(160) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

START TRANSACTION;

INSERT INTO cultural_men (id, hanzi, region, place, title, body, source_title, source_section, source_url, verification_status, material_use) VALUES
  ('men-1', '门／門', '大陆', '福建泉州', '除夕贴春联', '地方年俗资料将除夕贴春联列为一项习俗。', '新春忆旧俗', '除夕贴春联', 'https://www.quanzhou.gov.cn/lyb/mfms/ssms/200901/t20090123_3174.htm', '来源已定位', '中文摘要；不转载原图，引用时附出处'),
  ('men-2', '门／門', '台湾', '台湾（辞典所载）', '门左右贴春联', '辞典记录大门两边贴春联，门扇也可贴二字联。', '台湾民俗文物辞典', '春节布置', 'https://dict.th.gov.tw/detailPage.aspx?Ca=302&ID=1457', '来源已定位', '中文摘要；不转载原图，引用时附出处'),
  ('men-3', '门／門', '香港', '香港', '写挥春迎新', '平台采访说明挥春写上吉祥字句，寄托对家人的祝福。', '春节习俗重视家庭团圆', '第2节 貼揮春', 'https://www.familyandwomen.gov.hk/tc/story/2025012012273736147.html', '来源已定位', '中文摘要；不转载原图，引用时附出处'),
  ('men-4', '门／門', '澳门', '澳门', '年末悬挥春贴门神', '咨询材料把悬挥春、贴门神放在年前大扫除之后。', '非遗名录公开咨询文本', '春节', 'https://www.gov.mo/zh-hant/wp-content/uploads/sites/4/2024/12/%E9%A0%85%E7%9B%AE%E5%88%97%E5%85%A5%E9%9D%9E%E9%81%BA%E5%90%8D%E9%8C%84%E5%85%AC%E9%96%8B%E8%AB%AE%E8%A9%A2-%E4%B8%AD%E6%96%87.pdf', '来源已定位', '中文摘要；不转载原图，引用时附出处'),
  ('men-5', '门／門', '海外', '新加坡', '用春联装点家里', '非遗条目把春联和写有吉祥字的红纸剪饰列入家庭春节布置。', 'Chinese New Year', '春节布置段落', 'https://www.roots.gov.sg/ich-landing/ich/chinese-new-year', '来源已定位', '中文摘要；不转载原图，引用时附出处')
ON DUPLICATE KEY UPDATE id = cultural_men.id;

INSERT INTO cultural_cha (id, hanzi, region, place, title, body, source_title, source_section, source_url, verification_status, material_use) VALUES
  ('cha-1', '茶', '大陆', '中国大陆（申报范围）', '以茶待客', '名录记录以茶迎接客人，饮茶也见于家中、茶馆和仪式。', 'Traditional tea processing techniques and associated social practices in China', '项目简介', 'https://ich.unesco.org/RL/traditional-tea-processing-techniques-and-associated-social-practices-in-china-01884', '来源已定位', '中文摘要；不转载原图，引用时附出处'),
  ('cha-2', '茶', '台湾', '台湾客家社群', '动手制作擂茶', '客家云条目收录庄台芳制作擂茶的记录。', '莊臺芳製作擂茶', '条目正文', 'https://cloud.hakka.gov.tw/Details?p=80523&pid=290056', '来源已定位', '中文摘要；不转载原图，引用时附出处'),
  ('cha-3', '茶', '香港', '香港', '到茶楼饮茶', '香港旅游发展局以饮茶介绍茶与点心的搭配。', 'Yum Cha', '正文', 'https://www.discoverhongkong.com/eng/place-to-go/travel.guide-yum-cha.html', '来源已定位', '中文摘要；不转载原图，引用时附出处'),
  ('cha-4', '茶', '澳门', '澳门', '点心配一壶茶', '澳门旅游局把吃点心时泡茶品尝的活动称为饮茶。', '中式点心及菜肴', '饮茶介绍', 'https://www.macaotourism.gov.mo/zh-hant/dining/taste-of-macao/chinese-dimsum-and-dishes', '来源已定位', '中文摘要；不转载原图，引用时附出处'),
  ('cha-5', '茶', '海外', '新加坡', '茶作为祭祖供品', '国家文物局资料记载，有些家庭在中元节祭祖时以茶叶作供品。', 'Making and Sharing of Tea', '祭祀用途段落', 'https://www.roots.gov.sg/ich-landing/ich/Making-and-Sharing-of-Tea', '来源已定位', '中文摘要；不转载原图，引用时附出处')
ON DUPLICATE KEY UPDATE id = cultural_cha.id;

INSERT INTO cultural_chuan (id, hanzi, region, place, title, body, source_title, source_section, source_url, verification_status, material_use) VALUES
  ('chuan-1', '船', '大陆', '福建厦门、泉州沿海', '沿海社区送王船', '联合申报条目将厦门湾和泉州湾沿海列为送王船习俗传承区域。', '送王船联合申报', '项目简介', 'https://ich.unesco.org/en/RL/ong-chun-wangchuan-wangkang-ceremony-rituals-and-related-practices-for-maintaining-the-sustainable-connection-between-man-and-the-ocean-01608', '来源已定位', '中文摘要；不转载原图，引用时附出处'),
  ('chuan-2', '船', '台湾', '台湾屏东东港', '迎王祭典中的王船', '东港迎王平安祭典以王船为重要仪式物件。', '東港迎王平安祭典', '条目正文', 'https://taiwangods.moi.gov.tw/Religious_Culture/html/landscape/1_0011.aspx?i=90', '来源已定位', '中文摘要；不转载原图，引用时附出处'),
  ('chuan-3', '船', '香港', '香港大澳', '龙舟沿水道游涌', '大澳传统龙舟协会在端午前后以龙舟接神、游涌，最后送神回庙。', '大澳游涌及龙舟竞渡', '游涌仪式', 'https://www.islands.gov.hk/sc/festival-tai-o-dragon-boat-water-parade.php', '来源已定位', '中文摘要；不转载原图，引用时附出处'),
  ('chuan-4', '船', '澳门', '澳门南湾湖', '端午龙舟竞渡', '澳门体育局赛事资料记录南湾湖龙舟赛设本地和国际组别。', '澳门国际龙舟赛', '赛事新闻', 'https://www.sport.gov.mo/zh/sites/dragonboat_sp/2026/id/929/nid/5694', '来源已定位', '中文摘要；不转载原图，引用时附出处'),
  ('chuan-5', '船', '海外', '马来西亚马六甲', '华人社群传承送王船', '联合申报条目将马六甲华人社群列为送王船习俗传承社区。', '送王船联合申报', '项目简介', 'https://ich.unesco.org/en/RL/ong-chun-wangchuan-wangkang-ceremony-rituals-and-related-practices-for-maintaining-the-sustainable-connection-between-man-and-the-ocean-01608', '来源已定位', '中文摘要；不转载原图，引用时附出处')
ON DUPLICATE KEY UPDATE id = cultural_chuan.id;

INSERT INTO cultural_deng (id, hanzi, region, place, title, body, source_title, source_section, source_url, verification_status, material_use) VALUES
  ('deng-1', '灯／燈', '大陆', '福建泉州', '针刺无骨灯', '泉州花灯有彩扎灯、刻纸灯、针刺无骨灯等制作类别。', '灯彩（泉州花灯）', '项目说明', 'https://www.ihchina.cn/project_details/14059', '来源已定位', '中文摘要；不转载原图，引用时附出处'),
  ('deng-2', '灯／燈', '台湾', '台湾（名录所载）', '竹纸工艺做花灯', '文化资产资料将花灯联系到传统照明器具和竹纸工艺。', '花灯制作', '项目说明', 'https://nchdb.boch.gov.tw/embed/assets/overview/traditionalCraft/20240403000001', '来源已定位', '中文摘要；不转载原图，引用时附出处'),
  ('deng-3', '灯／燈', '香港', '香港', '中秋看彩灯', '香港社区节目资料记录中秋彩灯会。', '丙午年中秋彩灯会', '活动介绍', 'https://www.cpo.gov.hk/zh-hk/event/tc-mid-autumn-lantern-carnival-2026/', '来源已定位', '中文摘要；不转载原图，引用时附出处'),
  ('deng-4', '灯／燈', '澳门', '澳门新街坊', '做鱼灯与花草纸灯', '澳门政府活动公告列出玲珑鱼灯和花草纸灯两个元宵手作坊。', '澳门新街坊周日办元宵活动', '手作坊段落', 'https://www.gov.mo/zh-hant/news/1122158/', '来源已定位', '中文摘要；不转载原图，引用时附出处'),
  ('deng-5', '灯／燈', '海外', '新加坡', '传统花灯制作', '国家文物局把传统中式灯笼制作收录为非遗项目。', 'Making of Traditional Chinese Lanterns', '项目简介', 'https://www.roots.gov.sg/ich-landing/ich/making-of-traditional-chinese-lanterns', '来源已定位', '中文摘要；不转载原图，引用时附出处')
ON DUPLICATE KEY UPDATE id = cultural_deng.id;

INSERT INTO cultural_yuan (id, hanzi, region, place, title, body, source_title, source_section, source_url, verification_status, material_use) VALUES
  ('yuan-1', '圆／圓', '大陆', '浙江宁波海曙', '老街长桌宴的年节饮食（待补汤圆细节）', '海曙区政府记录南塘老街年节长桌宴的地方饮食。', '长桌宴飘香南塘老街', '活动正文', 'https://www.haishu.gov.cn/col/col1229826296/art/2026/art_8dc2da0a59c97414d99a1f926ed83935.html', '待补直接证据', '中文摘要；不转载原图，引用时附出处'),
  ('yuan-2', '圆／圓', '台湾', '台湾（文献馆所载）', '元宵吃汤圆', '台湾文献馆将吃汤圆、赏花灯、猜灯谜列为元宵习俗。', '元宵夜', '民俗说明', 'https://www.th.gov.tw/Epaper_Content/237/10008/', '来源已定位', '中文摘要；不转载原图，引用时附出处'),
  ('yuan-3', '圆／圓', '香港', '香港', '元宵节的汤圆', '香港教育局阅读材料以农历正月十五的元宵习俗介绍汤圆。', '农历正月十五是中国传统的元宵节', '阅读材料', 'https://sense.edb.gov.hk/uploads/content/spld/chinese_read_write_summer_2.pdf', '来源已定位', '中文摘要；不转载原图，引用时附出处'),
  ('yuan-4', '圆／圓', '澳门', '澳门旅游学院', '动手搓汤丸过元宵', '澳门旅游学院春节活动记录学生动手制作汤丸。', '承传中华文化 澳旅院一系列新春活动送鼠迎牛', '元宵汤丸活动段落', 'https://www.gov.mo/zh-hant/news/367523/', '来源已定位', '中文摘要；不转载原图，引用时附出处'),
  ('yuan-5', '圆／圓', '海外', '新加坡', '春节团圆饭', '国家文物局条目将团圆饭描述为新加坡华人春节家庭活动，案例聚焦团圆的含义。', 'Chinese New Year', '团圆饭段落', 'https://www.roots.gov.sg/ich-landing/ich/chinese-new-year', '来源已定位', '中文摘要；不转载原图，引用时附出处')
ON DUPLICATE KEY UPDATE id = cultural_yuan.id;

COMMIT;
SELECT 'men' AS case_table, COUNT(*) AS records, COUNT(DISTINCT region) AS regions FROM cultural_men;
SELECT 'cha' AS case_table, COUNT(*) AS records, COUNT(DISTINCT region) AS regions FROM cultural_cha;
SELECT 'chuan' AS case_table, COUNT(*) AS records, COUNT(DISTINCT region) AS regions FROM cultural_chuan;
SELECT 'deng' AS case_table, COUNT(*) AS records, COUNT(DISTINCT region) AS regions FROM cultural_deng;
SELECT 'yuan' AS case_table, COUNT(*) AS records, COUNT(DISTINCT region) AS regions FROM cultural_yuan;
