# Mac Game Rigger Alpha Eksiklik Raporu ve Ilerleme Rotasi

Tarih: 2026-06-16  
Repo durumu: `40a63d2` sonrasindaki alpha kanitlari baz alindi.  
Odak: Eksikleri netlestirmek, production seviyesine giderken hangi bosluklarin once kapatilacagini belirlemek.

## Kisa Sonuc

Mac Game Rigger su anda "calisan alpha" seviyesinde. Blender add-on akisi, landmark, armature generation, weight bind, cleanup, pose test, QA raporu, preview, Unity/Unreal FBX export operatorleri, paketleme ve Unity import verifier mevcut.

Ama bu henuz "oyun ekibinin yaz boyunca guvenle ana rigleme araci yapacagi production tool" seviyesi degil. En buyuk fark burada:

- Teknik pipeline geciyor.
- Gercek asset deformasyon kalitesi henuz kanitlanmis degil.
- Unity import bir kez dogrulandi.
- Unreal import dogrulanmadi.
- Artist UX hizlandirildi ama henuz akiskan degil.
- QA raporu sayisal/strukturel; gozle gorulen deformasyon kalitesini otomatik olcmuyor.

Bu yuzden dogru strateji: yeni buyuk ozellik eklemeden once "gercek asset kanit seti + engine import + deformasyon scoring" ucgenini kapatmak.

## Su Anda Guclu Oldugumuz Noktalar

1. Blender add-on temeli var.
   - Add-on kurulabiliyor.
   - Panel/operator mimarisi calisiyor.
   - Headless Blender testleriyle temel operatorler dogrulandi.

2. Deterministik rig pipeline var.
   - Landmark olusturma, temizleme, validasyon ve mirror akisi mevcut.
   - Humanoid ve quadruped template mantigi var.
   - Armature generation ve bone roll fix calisiyor.

3. Weight tarafinda alpha icin yeterli baslangic var.
   - Blender automatic weights operatoru var.
   - Capsule distance fallback weight operatoru var.
   - Weight cleanup operatoru influence limit, bos grup temizligi, prune ve normalize yapiyor.

4. QA ve export baslangici var.
   - Pose test operatorleri var.
   - QA JSON raporu var.
   - Preview PNG operatoru var.
   - Unity ve Unreal FBX export profilleri var.

5. Release disiplini basladi.
   - `docs/release-checklist.md` var.
   - `docs/alpha-smoke-results.md` var.
   - `dist/MacGameRigger-0.1.0.zip` paketi uretilmis.
   - Unity batchmode import verifier sandbox disinda pass verdi.

## Kritik Eksikler

### 1. Gercek production karakter deformasyonu kanitlanmadi

Mevcut full workflow smoke testleri generated proxy sahnelerle yapildi. Bu iyi bir teknik pipeline kaniti, fakat oyun uretimi icin yeterli degil.

Eksik olan:

- Lisansli veya public kullanima uygun gercek karakter asset seti.
- Bu assetlerde full rig workflow calistirilmis kanit.
- Pose screenshotlari.
- Weight cleanup oncesi/sonrasi fark.
- Artist tarafindan 1-5 kalite skoru.
- Fail case dokumantasyonu.

Risk:

Proxy meshlerde gecen bir pipeline, gercek karakterlerde omuz, kalca, diz, bilek, kuyruk, kanat, etek, palto, uzun sac ve aksesuar bolgelerinde zayif kalabilir.

Karar:

V1'e gitmeden once en az 10 gercek asset uzerinde deformasyon scorecard sart.

### 2. QA raporu deformasyon kalitesini olcmuyor

QA raporu su anda daha cok structural/count-based:

- Kemik sayisi.
- Vertex group durumu.
- Influence sayilari.
- Eksik/uyumsuz veri.

Bu gerekli ama yetersiz. Oyunda bizi asil yakacak seyler:

- Omuz cokmesi.
- Dirsek/diz patlamasi.
- Bilek burulmasi.
- Boyun kirilmasi.
- Kalca/leg clipping.
- Kuyruk/kanat yuzeyinin kopuk hareketi.
- Low-poly assetlerde yanlis agirlik dagilimi.

Eksik olan:

- Pose bazli visual deformation scoring.
- Kritik joint bolgeleri icin lokal mesh hareket analizi.
- Symmetry deviation raporu.
- "Bu rig production review'a gider/gitmez" karari.

Karar:

QA raporu V1 icin sadece teknik checklist olmamali; deformation review dashboard'a donmeli.

### 3. Unreal import dogrulanmadi

Unity tarafinda bir import verifier pass var. Unreal tarafinda `UnrealEditor` path/PATH yok, bu yuzden gerçek import kaniti yok.

Eksik olan:

- Unreal Editor path discovery.
- Unreal batch import script.
- Skeleton, mesh, material ve scale/orientation kontrolu.
- Log parse ile pass/fail sonucu.
- En az 1 humanoid ve 1 quadruped FBX import kaniti.

Risk:

FBX export operatoru calissa bile Unreal import tarafinda bone orientation, scale, root bone, leaf bone, axis veya material problemleri cikabilir.

Karar:

Beta gate icin Unreal import pass zorunlu olmali.

### 4. Unity import tek asset seviyesinde

Unity verifier calisiyor, ama sadece generated Unity FBX export adayinda dogrulandi.

Eksik olan:

- En az 3 farkli assette Unity import.
- Humanoid avatar mapping kontrolu.
- Generic rig kontrolu.
- Scale/orientation regression.
- Animation clip import smoke.

Risk:

Unity "import etti" demek, rig oyunda dogru calisacak demek degil. Avatar mapping ve transform konvansiyonlari ayrica dogrulanmali.

Karar:

Unity gate "FBX import pass" ile sinirli kalmamali; humanoid/generic mapping ve sahneye instantiate smoke da eklenmeli.

### 5. Blender 4.2 hedefi ile test edilen Blender versiyonu ayrismis olabilir

Urun hedefi Blender 4.2 macOS add-on. Fakat mevcut lokal dogrulamalar Blender 4.5.10 LTS uzerinden gecmis durumda.

Eksik olan:

- Blender 4.2 LTS ile ayni test matrisi.
- Blender 4.3/4.4/4.5 uyumluluk notu.
- Add-on API farklarinin listesi.

Risk:

Add-on hedef pazarda Blender 4.2 kullanan ekiplerde ufak API farklariyla bozulabilir.

Karar:

Alpha release notu "tested on 4.5.10" diye net olmali; V1'e giderken 4.2 compatibility matrix tamamlanmali.

### 6. Artist UX hala fazla manuel

Pipeline calisiyor ama hiz hedefi icin artist'in her assette manuel karar verme yuku dusmeli.

Eksik olan:

- Landmark wizard.
- Mesh tipine gore template onerisi.
- Landmarks save/load.
- Batch asset evaluation.
- Hata mesajlarinin artist diline cevrilmesi.
- Tek panelde "next action" yonlendirmesi.

Risk:

Teknik olarak calisan arac, artist icin yavas veya guvensiz hissederse yaz production planinda kullanilmaz.

Karar:

V1 farki "AI magic" degil; macOS'ta hizli, olculebilir, tekrar edilebilir rig workflow olmali.

### 7. Kanat, kuyruk, prop ve aksesuar destegi zayif

Dokumanlarda wing/prop-specific helper yok deniyor. Finger rigging, cloth/skirt, advanced tail/wing controls V1 disi tutulmus.

Bu dogru bir scope karari olabilir, ama oyun gelistirme hedefinde asset cesitliligi yuksekse risk yaratir.

Eksik olan:

- Basit prop attachment bones.
- Tail chain template.
- Wing chain template.
- Finger minimal template karari.
- Cloth/skirt icin "out of scope ama nasil handle edilir" kilavuzu.

Risk:

Humanoid + quadruped disindaki karakterler icin ekip tekrar manuel Blender isine donebilir.

Karar:

V1 kapsaminda en azindan prop attachment ve simple tail chain olmali. Advanced wing/cloth V2'ye kalabilir.

### 8. Real asset veri yonetimi yok

Gercek assetlerle test yapacaksak lisans, storage ve tekrar edilebilirlik lazim.

Eksik olan:

- `samples/manifest.json` veya benzeri asset manifest.
- Asset lisans bilgisi.
- Download/source URL.
- Hangi assetin hangi testte kullanildigi.
- Generated vs real asset ayrimi.
- Repo'ya koyulamayacak assetler icin local path strategy.

Risk:

Bugun gecen smoke yarin ayni sekilde tekrar edilemezse urun kalitesi takip edilemez.

Karar:

Beta oncesi asset manifest ve evidence folder standardi sart.

### 9. CI yok veya yeterince gorunur degil

Local testler geciyor, ama release guveni icin CI gerekiyor.

Eksik olan:

- Unit test CI.
- Add-on package CI.
- Blender headless smoke CI veya local-only documented gate.
- macOS runner stratejisi.
- Unity/Unreal import icin manuel gate mi CI gate mi karari.

Risk:

Her degisiklikte pipeline sessizce bozulabilir.

Karar:

Kisa vadede full engine CI sart degil; ama Python tests + package + Blender smoke en azindan release checklist'e baglanmali.

### 10. Performance ve buyuk mesh davranisi bilinmiyor

Proxy sahneler kucuk. Gercek oyun karakterlerinde mesh sayisi, vertex sayisi ve materyal sayisi daha yuksek olabilir.

Eksik olan:

- 10k / 50k / 100k vertex benchmark.
- Multi-mesh character benchmark.
- Weight cleanup runtime olcumu.
- Preview render runtime olcumu.
- Export runtime olcumu.

Risk:

Arac dogru calisir ama yavas kalirsa "hizli rigleme" vaadini karsilamaz.

Karar:

V1 icin performans hedefi: tipik game character assetinde full assisted workflow 10 dakikanin altinda kalmali; tool operatorleri tek tek saniyeler-dakikalar bandinda olculmeli.

## Onceliklendirilmis Ilerleme Rotasi

### Faz 0 - Alpha kanitlarini sertlestirme

Sure: 1-2 gun  
Hedef: "Calisiyor" iddiasini tekrar edilebilir hale getirmek.

Yapilacaklar:

1. Blender 4.2 ile ayni testleri calistir.
2. Blender 4.5.10 sonucunu ayri uyumluluk satiri olarak yaz.
3. Unity verifier dokumanini ayri dosyaya cikar.
4. `dist/MacGameRigger-0.1.0.zip` paket icerigini release checklist'e sabitle.
5. Install guide yaz.
6. Local-only engine verification notlarini netlestir.

Cikis kriteri:

- Alpha paketi temiz kuruluyor.
- Blender 4.2 veya hedef versiyon farki acikca dokumante.
- Unity import verification adimlari tekrar edilebilir.

### Faz 1 - Gercek asset validation pack

Sure: 3-5 gun  
Hedef: Proxy yerine gercek assetlerde kaliteyi gormek.

Yapilacaklar:

1. 10 assetlik test paketi sec.
2. Assetleri su gruplara ayir:
   - 3 humanoid.
   - 2 quadruped.
   - 1 low-poly humanoid.
   - 1 thin-limb humanoid.
   - 1 bulky/wide-shoulder humanoid.
   - 1 tail creature.
   - 1 accessory/prop-heavy character.
3. Her asset icin manifest kaydi ekle.
4. Her assette full workflow calistir.
5. QA JSON, preview PNG, FBX ve engine import sonucu sakla.
6. Artist score ekle.

Cikis kriteri:

- En az 10 real asset row'u dolu.
- En az 3 asset Unity'de import pass.
- En az 1 asset Unreal'da import pass veya Unreal blocker net.
- En az 70% asset "internal usable with cleanup" seviyesinde.

### Faz 2 - Deformation quality layer

Sure: 1-2 hafta  
Hedef: QA raporunu gercek rig kalitesi aracina cevirmek.

Yapilacaklar:

1. Pose bazli screenshot seti standardize et.
2. Deformation scoring rubric yaz.
3. Critical joint listesi olustur:
   - shoulder.
   - elbow.
   - wrist.
   - hip.
   - knee.
   - ankle.
   - neck.
   - tail base.
   - wing root.
4. QA raporuna per-joint issue list ekle.
5. Symmetry deviation metric ekle.
6. Influence heatmap veya vertex group outlier raporu ekle.
7. "Auto-fix suggested" bolumu ekle.

Cikis kriteri:

- QA raporu sadece "pass/fail" degil, "neresi bozuk ve nasil duzeltilir" soyluyor.
- Artist review suresi azaltilabiliyor.

### Faz 3 - Artist hiz ve UX

Sure: 1 hafta  
Hedef: Her assette manuel ugrasi azaltmak.

Yapilacaklar:

1. Landmark wizard.
2. Template auto-suggestion.
3. Landmark save/load.
4. One-click "Analyze -> Landmarks -> Armature -> Weights -> QA -> Preview" guided flow.
5. Hata mesajlarini sade hale getir.
6. Batch report paneli.

Cikis kriteri:

- Yeni bir assette ilk rig denemesi 5-10 dakika icinde cikiyor.
- Artist hangi adimin eksik oldugunu panelden goruyor.

### Faz 4 - Engine export hardening

Sure: 1 hafta  
Hedef: Unity ve Unreal'da import edilen assetlerin oyuna alinabilir oldugunu kanitlamak.

Yapilacaklar:

1. Unity avatar/generic rig checker.
2. Unity scene instantiate smoke.
3. Unity animation clip import smoke.
4. Unreal batch import checker.
5. Scale/orientation/root bone regression.
6. Export profile snapshot tests.

Cikis kriteri:

- Unity: 3 real asset pass.
- Unreal: 1 humanoid + 1 non-humanoid pass.
- Export ayarlari dokumante ve testli.

### Faz 5 - V1 kapsamini genisletme

Sure: 2-4 hafta  
Hedef: Oyun ekibinin yaz boyunca en cok karsilasacagi asset tiplerini karsilamak.

Yapilacaklar:

1. Finger minimal rig.
2. Prop attachment bones.
3. Tail chain helper.
4. Simple wing chain helper.
5. Cloth/skirt icin explicit "manual cleanup required" workflow.
6. Godot export karari.

Cikis kriteri:

- Humanoid ve quadruped disinda en az basit creature/prop workflow destekleniyor.
- V1 scope net: hangi asset otomatik, hangi asset assisted, hangi asset manual.

## Karar Kapilari

### Internal Alpha Gate

Durum: Buyuk olcude gecildi.

Sartlar:

- Add-on kuruluyor.
- Headless testler geciyor.
- Package uretiliyor.
- En az bir Unity import verifier pass var.
- Known issues dokumante.

Eksik kalan:

- Blender 4.2 uyumluluk kaniti.
- Install guide.
- Engine verification dokumaninin ayrilmasi.

### Production Trial Gate

Bu gate henuz gecilmedi.

Sartlar:

- 10 gercek asset workflow row'u.
- 3 Unity import pass.
- 1 Unreal import pass.
- Her asset icin preview PNG.
- Her asset icin QA JSON.
- Deformation scoring rubric.
- Artist tarafindan "usable with cleanup" skoru en az 70%.

### Beta Gate

Bu gate icin daha is var.

Sartlar:

- Blender 4.2 ve 4.5 compatibility matrix.
- CI veya documented local release gate.
- Unity ve Unreal import regression.
- Landmark wizard.
- Save/load landmark sets.
- QA report deformation layer.
- En az 2 farkli Mac cihazinda smoke.

### V1 Gate

Sartlar:

- 20+ real asset benchmark.
- Humanoid ve quadruped workflow production trial'da kullanilmis.
- Export profilleri oyun projesinde denenmis.
- Artist dokumantasyonu tamam.
- Known limitations net ve kabul edilebilir.

## Ilk 10 Somut Is

1. `docs/install-guide.md` yaz.
   - Blender add-on install.
   - Dev symlink install.
   - Zip install.
   - macOS izinleri.

2. `docs/unity-import-verification.md` yaz.
   - Unity path.
   - Sandbox disi calistirma.
   - Licensing Client notu.
   - Pass/fail log ornekleri.

3. `docs/unreal-import-verification.md` yaz.
   - Unreal path discovery.
   - Batch import hedefi.
   - Eksik ortam blocker'i.

4. `docs/asset-evaluation-protocol.md` yaz.
   - Asset secim kriterleri.
   - Workflow adimlari.
   - Evidence naming.
   - Artist score.

5. `samples/manifest.json` baslat.
   - Asset ID.
   - Source.
   - License.
   - Category.
   - Expected risk.

6. `docs/deformation-scoring-rubric.md` yaz.
   - 1-5 skor.
   - Kritik jointler.
   - Pass/fail esikleri.

7. `scripts/run_full_alpha_smoke.sh` ekle.
   - Unit tests.
   - Blender smoke tests.
   - Package.
   - Optional Unity verifier.

8. QA raporunu genislet.
   - Per-joint warnings.
   - Symmetry issue list.
   - Influence outlier summary.

9. Landmark UX'i iyilestir.
   - Save/load.
   - Wizard.
   - Template suggestion.

10. Unreal verifier tasarla ve ilk path check'i ekle.
   - `UnrealEditor` bulunamazsa actionable mesaj.
   - Bulunursa batch import smoke.

## Acik Riskler

1. Otomatik rigleme beklentisi yanlis yonetilirse hayal kirikligi yaratir.
   - Bu urun "tek tikla production rig" degil.
   - Dogru konum: Mac-first assisted rigging workbench.

2. Gercek assetler proxylerden cok daha kirli olacak.
   - Non-manifold mesh.
   - Mixed transforms.
   - Coklu mesh.
   - Aksesuar.
   - Asimetrik model.

3. Engine import pass kalite pass degildir.
   - Unity/Unreal asseti ice alabilir ama animasyonda bozulma olabilir.

4. Scope sisirme riski var.
   - Finger, cloth, wing, facial rig, IK/FK, retargeting hepsi ayni anda alinmamali.

5. CUDA'siz hedef dogru, ama ML tabanli otomasyon beklentisi sinirli tutulmali.
   - Avantajimiz deterministic Blender workflow + iyi UX + engine-safe export olmali.

## Net Tavsiye

Bir sonraki sprintte yeni buyuk rig feature eklemeyin. Once kanit tabanini sertlestirin:

1. Install/verification dokumanlarini tamamla.
2. 10 real asset validation pack olustur.
3. Unity importu 3 assete cikar.
4. Unreal import blocker'ini kaldir.
5. Deformation scoring rubric'i ekle.

Bunlar bittiginde elimizde gercek karar verilebilir tablo olacak:

- Bu tool yaz production'inda hangi assetlerde ise yarar?
- Nerede artist cleanup gerekir?
- Nerede manuel Blender workflow'a donmek gerekir?
- V1'e hangi feature girmeli, hangisi V2'ye kalmali?

Su anki en dogru hedef: "Production-ready rigger" iddiasindan once "production trial-ready assisted rigger" seviyesine cikmak.
