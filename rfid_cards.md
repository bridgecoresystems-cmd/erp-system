Параметры подключения
База данных: factory_erp_db
Пользователь: erp_user
Пароль: [REMOVED FOR SECURITY]
Хост: localhost
Порт: 5432

GitHub Token: [REMOVED FOR SECURITY]

https://github.com/bridgecoresystems-cmd/erp-system


daphne -b 0.0.0.0 -p 8000 factory_erp.asgi:application

card N1 - A38B3B1C
card N2 - F1D31804
card N3 - 0134FE03
card N4 - 049178C92B0289
card N5 - 23690204
card N6 - 045190CA2B0289

const char* ssid = "[YOUR_WIFI_SSID]";
const char* password = "[YOUR_WIFI_PASSWORD]";

// ===== НАСТРОЙКИ СЕРВЕРА =====
const char* server_url = "http://192.168.1.101:8000";
const char* esp32_id = "LOHIA-001";

kosnulsa kartoy status obnowilsya byl prostoy teper rabotaet poyawilos imya operatora. nazhimayu na knopku cherez tri sekundy wyzow mastera da(do etogo net) no imya operatora ischezaet(tak ne dolzhno byt) status ne pomenyalsya(dolzhen menyatsa). master prishel kosnulsa kartoy statsu rabotaet poyawilos imya sotrudnika, wyzow mastera stalo net. kosnulsya wtoroy raz status remont wyzow mastera net master imya tozhe net. teper opyat kogda stanok byl w prsotye kosnulsya kartoy operatora wse poyawilos imya operatora, status rabotaet. kogda obnowil F5 imya operatora ischezlo??? pri nazhatii na knopku zametil chto websocket otklyuchilsa. kak goworil ranshe imya operatora propalo. kosnulsa kartoy mastera/mehanika i obnowil stranicu F5: status: remont, imya operatora ischezlo, wyzow mastera: remont,imya mastera poyawilos. potom opyat kosnulsa kartoy mastera (wtroye kasaniye eto master otremontirowal.) imya operatora poyawilos, wyzow mastera ischez. status remont. F5 status obnowilsa rabotaet imya operatora ischezlo. pochemu wse tak slozhno gde mne i kak wse isprawit???

@maintenance pri nazhatii na knopku wyhodit data, wremya wyzowa, operator, status-ozhidayet, opisaniye-wyzow stanka Станок Lohia #1
mehanik prishel kosnulsya kartoy, chto pomenyalos:  master-imya poyawilos, status-w rabote, wremya reakcii ne pokazywaet
wtoroy raz kasayeshsya kartoy wse zapisi ischezayut.
dlya sprawki kogda nazhimayesh na F5 meklayut wse zapisi na dolyu sekundu potom ischezayut. a tak nikakih zapisey ne widno. eto kazhetsa izza websocket. peresmotri logiku.
ty yedinstwenniy ii kotoriy superski sprawlyayetsa s logikoy na urra

metrazhi
@dashboard pri zakrytii smeny operator ischez no metrazh ostalsya, metrazh tozhe dolzhen ischeznut. u menya takoe oshuhseniye chto metrazhi ne podklyucheny k websocket
@shifts dlitelnost wremeni nado isprawit ono pokazywaet chasy i eto ne ochen ponyatno.websocket tut woobshe ne rabotaet nado wse delat w ruchnuyu cherez F5 posmene kazhetsya wse koroche sam tozhe posmotrish
@machine zdes tozhe tak websocket woobshe ne rabotayet. 
AttributeError: 'LohiaConsumer' object has no attribute 'get_active_shifts'
status stanka: stanok rabotaet operatora ne pokzywaet pri nazhatii F5 imya melkayet
aktiwnaya smena: tut operatora pokazywayut no dlitelnost wremeni hramayet net minut yest chasy neponyatno
wyzow mastera pri nazhatii na knopku nichego ne proishodit tolko posle F5 poyawlyetsa status:ozhidaniye, pri kasanii karty nado obnowit stranicu cherez F5, tolko potom poyawlyayetsa imya mastera takzhe pri powtornom kasanii nado F5 nazhimat.
posledniye impulsy tozhe nado obnowlyat cherez F5
posledniye smeny: tozhe F5, no tut yest dlitelnost w minutah eto ochen horosho ne w chasah,
wremya reakcii: tozhe cherez F5 obnowlyat nado, tam wremya reakcii i wremya remonta w minutah i sekundah, mozhet minuty i sekundy i chasy. chtoby rabotalo horosho a ne 01:75:96 delitel dolzhen byt 60 a ne 100 :)
