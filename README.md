<div align="center">

# FaraidFlow

**Kalkulator pewarisan Islam (faraid)**

[English](README.en.md) · Bahasa Indonesia

[![Status: beta](https://img.shields.io/badge/status-beta-orange)](#status)

</div>

---

Kalkulator pembagian warisan Islam. Masukkan nilai harta dan siapa saja yang
meninggalkan pewaris, lalu aplikasi menghitung bagian setiap ahli waris,
menampilkan alasannya, dan menandai ahli waris yang **terhalang (hajb)** untuk
menerima warisan.

Dua bahasa: **Indonesia** dan **Inggris**.

> **Ini masih beta.** Angka dihitung mengikuti kaidah faraid Sunni, tapi
> tetaplah konfirmasi hasilnya kepada ahli hukum atau tokoh agama yang Anda
> percaya sebelum memakainya untuk pembagian warisan sungguhan. Aplikasi ini
> bukan pengganti nasihat hukum.

## Status

Saat ini **hanya layar "Hitung"** yang berfungsi. Menu **Informasi** dan
**Tentang** sudah ada di beranda tapi masih menampilkan "Segera hadir".

## Fitur

**Harta (harta pusaka)**

- Nilai total aset
- Biaya pemakaman
- Utang
- Wasiat — dibatasi maksimal **1/3** harta, dan aplikasi memberi tahu kalau
  wasiat yang dimasukkan melebihi 1/3

**Ahli waris**

- Suami / istri / tidak ada
- Anak
- Orang tua
- Saudara

Masing-masing diisi dengan **jumlah orang**, jadi keluarga besar cepat diinput.

**Hasil**

- Tabel bagian setiap ahli waris: pecahan, jumlah rupiah, dan jumlah per orang
- Pohon waris — ahli waris dikelompokkan per cabang, dengan akar pewaris
- Rincian perhitungan: setiap bagian disamakan penyebutnya lalu dijumlahkan
  sampai `n/lcm = 1`
- **Ahli waris terhalang (hajb)** — siapa yang gugur dan alasannya
- Deteksi **'aul** (pembagian melebihi 1) dan **radd** (sisa dikembalikan ke
  ahli waris yang entitled)

## Cara memakai

1. Buka aplikasi, lalu tekan **Hitung**.
2. Isi data harta di bagian atas.
3. Pilih ada atau tidaknya pasangan, lalu isi jumlah anak, orang tua, dan
   saudara.
4. Tekan tombol hitung. Tabel, pohon waris, dan rincian muncul di bawah.

Ganti bahasa lewat tombol di kanan atas.

## Catatan perhitungan

- Utang **tidak diwariskan**. Utang menempel pada harta pusaka dan dilunasi
  lebih dulu sebelum sisa dibagikan. Ahli waris tidak wajib membayar utang
  pewaris, tetapi boleh melakukannya.
- Perhitungan mengikuti kaidah Sunni yang umum digunakan. Untuk kasus yang
  masih diperdebatkan atau belum disepakati, pilihan yang dipakai proyek ini
  terdokumentasi di `src/app/calculation/`.

Dua hal yang perlu diketahui karena **berbeda dari sebagian mazhab**:

- **Radd dikembalikan kepada ahli waris dengan bagian tetap, kecuali pasangan.**
  Ini mengikuti konvensi yang dipakai proyek ini. Sebagian mazhab mengembalikan
  radd kepada semua pihak yang berhak, termasuk pasangan.
- Kalau setelah semua yang berhak hanya **pasangan** yang tersisa, sisa
  pembagiannya dikosongkan dan aplikasi meminta Anda **meminta panduan
  hukum/fiqh**. Kasus seperti ini tidak diselesaikan otomatis.

Kontribusi untuk kasus seperti ini sangat diterima — buka issue dulu sebelum
mengirim patch.

## Mengunduh

Repo ini publik dan semua builds-nya gratis, dibuat otomatis oleh GitHub
Actions.

| Platform | Cara |
|---|---|
| **Android** | Unduh `.apk` dari [halaman Releases](https://github.com/Naylings/ahli-waris/releases), buka, lalu izinkan **Install unknown apps** untuk aplikasi yang membukanya. |
| **Windows** | Unduh `.zip` dari [halaman Releases](https://github.com/Naylings/ahli-waris/releases), ekstrak, jalankan `ahli-waris.exe`. |
| **Web** | Buka <https://naylings.github.io/ahli-waris/> — tanpa perlu unduh apa pun. |

### Peringatan Android & Windows

APK dan EXE **ditandatangani dengan debug key**, bukan sertifikat rilis.
Artinya:

- Android akan memperingatkan "sumber tidak dikenal" — itu normal, pilih
  **Install anyway**.
- Windows SmartScreen bisa menampilkan "Windows protected your PC" — pilih
  **More info → Run anyway**.

Keduanya aman untuk dipakai dan dibagikan, tapi **tidak bisa** dikirim ke Google
Play. Untuk distribusi Play Store nanti perlu keystore rilis.

## Menjalankan dari sumber

Butuh Python 3.10+ dan [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/Naylings/ahli-waris.git
cd ahli-waris
uv sync
uv run flet run
```

Versi web:

```bash
uv run flet run --web
```

## Pengembangan

```bash
uv sync
uv run pytest          # 146 tes
uv run ruff check src
```

> **Catatan:** Flet 1.0.1 hanya bisa dibangun dengan Flutter 3.44.8. Versi
> Flet dan Flutter di-pin persis di `pyproject.toml` dan
> `.github/workflows/release.yml`. Kalau salah satu diubah, yang lain harus
> ikut diubah.

### Struktur

| Path | Isi |
|---|---|
| `src/app/calculation/` | Mesin perhitungan. Python murni, tanpa UI, tanpa import Flet. |
| `src/app/localization/` | String bahasa Indonesia dan Inggris. |
| `src/app/pages/` | Layar aplikasi. |
| `src/app/components/` | Widget yang dipakai bersama. |

Mesin perhitungan tidak bergantung sama sekali pada UI, jadi kaidahnya bisa
diuji langsung.

## Lisensi

MIT — lihat [LICENSE](LICENSE).
