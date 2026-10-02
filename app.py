
from flask import Flask, render_template, request, make_response
import json

import pyodbc

app=Flask(__name__)


def tc_kimlik_dogrulama(kimlik_no):
    #11 haneli ve sadece rakamlardan olmalı
    if len(kimlik_no) != 11:
        return False
    if not kimlik_no.isdigit():
        return False

    # İlk hane 0 olamaz
    if kimlik_no[0] == '0':
        return False

    # karakteri int'e çevir
    
    rakamlar=[int(kimlik_no[k]) for k in range(11)]
    #10. hane kontrolü
    tek_toplam=rakamlar[0]+rakamlar[2]+rakamlar[4]+rakamlar[6]+rakamlar[8]

    cift_toplam=rakamlar[1]+rakamlar[3]+rakamlar[5]+rakamlar[7]

    onuncu_hane=(tek_toplam *7-cift_toplam)%10

    if onuncu_hane != rakamlar[9]:
        return False

    ilk_on_toplam=sum(rakamlar[:10])
    if ilk_on_toplam % 10 != rakamlar[10]:
        return False


    return True


def get_db_connection():
    connection = pyodbc.connect(
        'DRIVER={SQL Server};'
        'SERVER=LAPTOP-HPSARE;'
        'DATABASE=NUFUS;'
        'Trusted_Connection=yes;'
    )
    return connection

@app.route('/')
def index():
    try:
        conn = get_db_connection()
        conn.close()
        mesaj = "Veritabanına bağlanıldı."
    except Exception as e:
        mesaj = f"Veritabanına bağlanılamadı: {str(e)}"
    return render_template('index.html', mesaj=mesaj)

@app.route('/ekle', methods=['POST'])
def ekle():

    kimlik_no = request.form.get('kimlik_no')
    isim = request.form.get('isim')
    soyisim = request.form.get('soyisim')
    kizlik_soyadi = request.form.get('kizlik_soyadi')
    dogum_tarihi = request.form.get('dogum_tarihi')
    sehir = request.form.get('sehir')
    cinsiyet = request.form.get('cinsiyet')
    olu_mu = request.form.get('olu_mu', default='H')
    kaydeden = "Admin"
    medeni_durum = request.form.get('medeni_durum')
    guncel_mi=1
    il=request.form.get('il')
    ilce=request.form.get('ilce')
    mahalle=request.form.get('mahalle')



    if not (cinsiyet=='K' and medeni_durum =="EVLI"):
        kizlik_soyadi=None

    if not tc_kimlik_dogrulama(kimlik_no):
        return '<div class="flex items-center justify-between p-4 mb-4 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg"><span>Geçersiz TC Kimlik Numarası! Lütfen kontrol edin.</span><button onclick="this.parentElement.remove()" class="ml-4 text-red-500 hover:text-red-800 font-bold text-lg leading-none">&times;</button></div>'

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM TBLVATANDASLAR WHERE RTRIM(KIMLIK_NO)=?",kimlik_no)
    sayi=cursor.fetchone()[0]
    if sayi>0:
        cursor.close()
        conn.close()
        return '<div class="flex items-center justify-between p-4 mb-4 text-sm text-yellow-700 bg-yellow-50 border border-yellow-200 rounded-lg"><span>Bu TC Kimlik numarası sistemde kayıtlı!</span><button onclick="this.parentElement.remove()" class="ml-4 text-yellow-500 hover:text-yellow-800 font-bold text-lg leading-none">&times;</button></div>'

    try:
        sorgu = "INSERT INTO TBLVATANDASLAR (KIMLIK_NO, ISIM, SOYISIM, KIZLIK_SOYAD, DOGUM_TARIH, SEHIR, CINSIYET, OLUM, KAYDEDEN, KAYIT_TARIH, MEDENI_DURUM) VALUES (?,?,?,?,?,?,?,?,?,GETDATE(),?)"
        cursor.execute(sorgu, kimlik_no, isim, soyisim, kizlik_soyadi, dogum_tarihi, sehir, cinsiyet, olu_mu, kaydeden, medeni_durum)
        conn.commit()

        cursor.execute(
            "INSERT INTO TBLADRES (KIMLIK_NO, SEHIR, ILCE, MAHALLE, GUNCEL_MI, BASLANGIC_TARIH) VALUES (?,?,?,?,1,GETDATE())",
            kimlik_no, sehir, ilce, mahalle
        )
        conn.commit()

        cursor.close()
        conn.close()
        return '<div class="flex items-center justify-between p-4 mb-4 text-sm text-green-700 bg-green-50 border border-green-200 rounded-lg"><span>Kayıt veri tabanına başarıyla eklendi.</span><button onclick="this.parentElement.remove()" class="ml-4 text-green-500 hover:text-green-800 font-bold text-lg leading-none">&times;</button></div>'

    except Exception as e:
        cursor.close()
        conn.close()
        return f'<div class="flex items-center justify-between p-4 mb-4 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg"><span>Hata: {str(e)}</span><button onclick="this.parentElement.remove()" class="ml-4 text-red-500 hover:text-red-800 font-bold text-lg leading-none">&times;</button></div>'
     


@app.route('/liste')
def liste():
    conn=get_db_connection()
    cursor=conn.cursor()
    cursor.execute("""
    --vatandasss
    SELECT RTRIM(V.KIMLIK_NO) AS KIMLIK_NO, V.ISIM, V.SOYISIM, V.KIZLIK_SOYAD, V.DOGUM_TARIH, 
    V.SEHIR, V.CINSIYET, V.OLUM, V.KAYDEDEN, V.KAYIT_TARIH, V.MEDENI_DURUM, V.DEGISTIREN, V.DEGISIM_TARIH,A.SEHIR,A.ILCE 
    FROM TBLVATANDASLAR V
    LEFT JOIN TBLADRES A ON RTRIM(V.KIMLIK_NO)=RTRIM(A.KIMLIK_NO) AND A.GUNCEL_MI=1""")
    vatandaslar=cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('liste.html', vatandaslar=vatandaslar)


@app.route('/olum-kaydi/<kimlik_no>',methods=['POST'])
def olum_kaydi(kimlik_no):
    conn=get_db_connection()
    cursor=conn.cursor()
    cursor.execute("UPDATE TBLVATANDASLAR SET OLUM = 'E' WHERE RTRIM(KIMLIK_NO)  = ?", kimlik_no)
    conn.commit()
    cursor.close()
    conn.close()
    return '<td class="py-3 pr-4 text-red-600 font-semibold">E</td>'

@app.route('/duzenle-form/<kimlik_no>')
def duzenle_form(kimlik_no):
    conn=get_db_connection()
    cursor=conn.cursor()
    cursor.execute("""SELECT RTRIM(KIMLIK_NO)AS KIMLIK_NO, ISIM,SOYISIM,
    KIZLIK_SOYAD,DOGUM_TARIH,SEHIR,CINSIYET,MEDENI_DURUM,
    OLUM FROM TBLVATANDASLAR WHERE RTRIM(KIMLIK_NO) = ?""", kimlik_no)
    v=cursor.fetchone()
       # Güncel adres (GUNCEL_MI=1)
    cursor.execute("""SELECT SEHIR, ILCE, MAHALLE FROM TBLADRES
        WHERE RTRIM(KIMLIK_NO) = ? AND GUNCEL_MI = 1""", kimlik_no)
    guncel_adres = cursor.fetchone()

    # Tüm adres geçmişi
    cursor.execute("""SELECT SEHIR, ILCE, MAHALLE, GUNCEL_MI, BASLANGIC_TARIH, BITIS_TARIH
        FROM TBLADRES WHERE RTRIM(KIMLIK_NO) = ?
        ORDER BY GUNCEL_MI DESC, BASLANGIC_TARIH DESC""", kimlik_no)
    adresler = cursor.fetchall()



    cursor.close()
    conn.close()
    return render_template('modal_duzenle.html', v=v,adresler=adresler,guncel_adres=guncel_adres)
    
@app.route('/vatandas-satir/<kimlik_no>')
def vatandas_satir(kimlik_no):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        --vatandas satir verisini çeker..
        SELECT RTRIM(v.KIMLIK_NO) AS KIMLIK_NO, v.ISIM, 
        v.SOYISIM, v.KIZLIK_SOYAD, v.DOGUM_TARIH, v.SEHIR,
        v.CINSIYET, v.OLUM, v.KAYDEDEN, v.KAYIT_TARIH,v.MEDENI_DURUM, v.DEGISTIREN, v.DEGISIM_TARIH,
        A.SEHIR, A.ILCE
        FROM TBLVATANDASLAR V 
        LEFT JOIN  TBLADRES A ON 
        RTRIM(V.KIMLIK_NO)=RTRIM(A.KIMLIK_NO) AND A.GUNCEL_MI=1
        WHERE RTRIM(V.KIMLIK_NO) = ?""" 
        ,kimlik_no
    )
    v = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('satir_listesi.html', vatandaslar=[v])

@app.route('/guncelle/<kimlik_no>',methods=['POST'])
def guncelle(kimlik_no):
    isim=request.form.get('isim')
    soyisim=request.form.get('soyisim')
    kizlik_soyadi=request.form.get('kizlik_soyadi')
    cinsiyet=request.form.get('cinsiyet')
    dogum_tarihi=request.form.get('dogum_tarihi')
    sehir=request.form.get('sehir')
    medeni_durum=request.form.get('medeni_durum')
    olum=request.form.get('olum','H')
    degistiren="Admin"

    #kızlık soyadı sorgulama 
    if not (cinsiyet=='K' and medeni_durum=='EVLI'):
        kizlik_soyadi=None

    conn=get_db_connection()
    cursor=conn.cursor()
    try:
        cursor.execute("""
            UPDATE TBLVATANDASLAR 
            SET ISIM=?, SOYISIM=?, KIZLIK_SOYAD=?, DOGUM_TARIH=?, CINSIYET=?, MEDENI_DURUM=?, OLUM=?,
                DEGISTIREN=?, DEGISIM_TARIH=GETDATE()
            WHERE RTRIM(KIMLIK_NO)=?
        """, (isim, soyisim, kizlik_soyadi, dogum_tarihi,
            cinsiyet, medeni_durum, olum, degistiren, kimlik_no))

        conn.commit()

        #güncel satır verisini çek
        cursor.execute("""
        --güncel satır verisini çek
        SELECT RTRIM(V.KIMLIK_NO) AS KIMLIK_NO, V.ISIM, V.SOYISIM,V.KIZLIK_SOYAD,
        V.DOGUM_TARIH,V.SEHIR,V.CINSIYET,
        V.MEDENI_DURUM,V.OLUM,V.KAYDEDEN,V.KAYIT_TARIH,
        V.DEGISTIREN,V.DEGISIM_TARIH, A.SEHIR, A.ILCE FROM TBLVATANDASLAR V
        LEFT JOIN TBLADRES A ON 
        RTRIM(V.KIMLIK_NO)=RTRIM(A.KIMLIK_NO)
        AND A.GUNCEL_MI=1
        WHERE RTRIM(V.KIMLIK_NO)=?
        """, kimlik_no)
        
        v = cursor.fetchone()

        satir_html = render_template('vatandas_satir.html', v=v)
        oob_satir = f'<tr id="satir-{kimlik_no}" hx-swap-oob="outerHTML:#satir-{kimlik_no}">{satir_html[satir_html.find("<td"):satir_html.rfind("</tr>")]}</tr>'

        modal_bildirim = '<div hx-swap-oob="innerHTML:#modal-bildirim"><div class="flex items-center justify-between bg-emerald-50 border border-emerald-200 text-emerald-700 px-4 py-2 rounded-lg text-sm font-medium"><span>&#x2705; Bilgiler ba\u015far\u0131yla kaydedildi.</span><button onclick="this.parentElement.remove()" class="ml-3 text-emerald-500 hover:text-emerald-800 font-bold text-lg leading-none">&times;</button></div></div>'

        response = make_response('<span></span>' + oob_satir + modal_bildirim)
        response.headers['HX-Trigger'] = json.dumps({
            'modalKapatGecikmeli': True,
            'gosterBildirim': 'Vatanda\u015f bilgileri g\u00fcncellendi.',
            'satirGuncelle': kimlik_no
        })
        return response
    except Exception as e:
        conn.rollback()
        return f'''<div role="alert" class="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg shadow-lg flex items-center justify-between gap-3">
            <span class="text-sm">{str(e)}</span>
            <button onclick="this.closest(\'[role=alert]\').remove()" class="text-red-600 hover:text-red-900 font-bold text-lg leading-none">&times;</button>
        </div>'''
    finally:
        cursor.close()
        conn.close()

        

@app.route('/adres-guncelle/<kimlik_no>', methods=['POST'])
def adres_guncelle(kimlik_no):
    sehir = request.form.get('SEHIR')
    ilce = request.form.get('ILCE')
    mahalle = request.form.get('MAHALLE')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Eski adresi geçmişe taşı
        cursor.execute("UPDATE TBLADRES SET GUNCEL_MI=0, BITIS_TARIH=GETDATE() WHERE RTRIM(KIMLIK_NO)=? AND GUNCEL_MI=1", (kimlik_no,))

        # 2. Yeni adres ekleme (HATA DÜZELTİLDİ: VALUES kelimesi eksikti, eklendi)
        cursor.execute("""
            INSERT INTO TBLADRES (KIMLIK_NO, SEHIR, ILCE, MAHALLE, GUNCEL_MI, BASLANGIC_TARIH) 
            VALUES (?, ?, ?, ?, 1, GETDATE())
        """, (kimlik_no, sehir, ilce, mahalle))

        # 3. Ana tablodaki şehir bilgisini de güncelle
        cursor.execute("UPDATE TBLVATANDASLAR SET SEHIR=?, DEGISTIREN='Admin', DEGISIM_TARIH=GETDATE() WHERE RTRIM(KIMLIK_NO)=?", (sehir, kimlik_no))
        
        # Değişiklikleri kaydet
        conn.commit()

        # 4. Modal'ın içine yeni verileri basmak için güncel bilgileri tekrar çekiyoruz
        cursor.execute("""
            SELECT RTRIM(V.KIMLIK_NO) AS KIMLIK_NO, V.ISIM, V.SOYISIM,
            V.KIZLIK_SOYAD, V.DOGUM_TARIH, V.SEHIR, V.CINSIYET, V.OLUM,
            V.KAYDEDEN, V.KAYIT_TARIH, V.MEDENI_DURUM, V.DEGISTIREN, V.DEGISIM_TARIH,
            A.SEHIR, A.ILCE
            FROM TBLVATANDASLAR V
            LEFT JOIN TBLADRES A ON RTRIM(V.KIMLIK_NO)=RTRIM(A.KIMLIK_NO) AND A.GUNCEL_MI=1
            WHERE RTRIM(V.KIMLIK_NO) = ?
        """, (kimlik_no,))
        v = cursor.fetchone()

        cursor.execute("SELECT SEHIR, ILCE, MAHALLE FROM TBLADRES WHERE RTRIM(KIMLIK_NO)=? AND GUNCEL_MI=1", (kimlik_no,))
        guncel_adres = cursor.fetchone()

        cursor.execute("SELECT SEHIR, ILCE, MAHALLE, GUNCEL_MI, BASLANGIC_TARIH, BITIS_TARIH FROM TBLADRES WHERE RTRIM(KIMLIK_NO)=? ORDER BY GUNCEL_MI DESC, BASLANGIC_TARIH DESC", (kimlik_no,))
        adresler = cursor.fetchall()

        response = make_response('<span></span>')
        response.headers['HX-Trigger'] = json.dumps({
            'modalKapat': True,
            'gosterBildirim': 'Adres bilgileri ba\u015far\u0131yla g\u00fcncellendi.',
            'satirGuncelle': kimlik_no
        })
        return response


    except Exception as e:
        # Bir hata olursa veritabanı işlemlerini geri al
        conn.rollback()
        return f"<div class='p-4 mb-4 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg'>Hata: {str(e)}</div>"

    finally:
        # try veya except fark etmeksizin en son bağlantıları GÜVENLE kapat
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()
@app.route('/ara')
def ara():
    q=request.args.get('q','').strip()
    conn=get_db_connection()
    cursor=conn.cursor()

    if q:
        arama=f'%{q}%'
        cursor.execute("""
        SELECT RTRIM(v.KIMLIK_NO) AS KIMLIK_NO, V.ISIM,
        V.SOYISIM, V.KIZLIK_SOYAD, V.DOGUM_TARIH, 
        V.SEHIR, V.CINSIYET, V.OLUM, V.KAYDEDEN, V.KAYIT_TARIH, V.MEDENI_DURUM, V.DEGISTIREN, V.DEGISIM_TARIH,
        A.SEHIR, A.ILCE, A.MAHALLE
        FROM TBLVATANDASLAR V
        LEFT JOIN TBLADRES A ON RTRIM(V.KIMLIK_NO)=RTRIM(A.KIMLIK_NO) AND A.GUNCEL_MI=1
        WHERE RTRIM(V.KIMLIK_NO) LIKE ? OR V.ISIM LIKE ? OR V.SOYISIM LIKE ?
        """, (arama, arama, arama))
        vatandaslar=cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('satir_listesi.html', vatandaslar=vatandaslar)

    else:
        cursor.execute("""
        SELECT RTRIM(V.KIMLIK_NO) AS KIMLIK_NO, V.ISIM, V.SOYISIM, V.KIZLIK_SOYAD, V.DOGUM_TARIH,
        V.SEHIR, V.CINSIYET, V.OLUM, V.KAYDEDEN, V.KAYIT_TARIH, V.MEDENI_DURUM, V.DEGISTIREN, V.DEGISIM_TARIH,
        A.SEHIR, A.ILCE
        FROM TBLVATANDASLAR V
        LEFT JOIN TBLADRES A ON RTRIM(V.KIMLIK_NO)=RTRIM(A.KIMLIK_NO) AND A.GUNCEL_MI=1
        ORDER BY KIMLIK_NO
        """)
        vatandaslar=cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('satir_listesi.html', vatandaslar=vatandaslar)






if __name__ == '__main__':
    app.run(debug=True)
