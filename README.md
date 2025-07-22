# FODDTRADER

Açık kaynak kodlu, otomatik sinyal işleyen ve Binance ile entegre çalışan bir masaüstü uygulamasıdır.

## Kurulum

1. Gerekli kütüphaneler:

   - python-binance
   - telethon

Kurulum:
```bash
pip install python-binance telethon
```
> Not: `tkinter` çoğu Python dağıtımında yüklüdür. Eğer eksikse Windows'ta `pip install tk` komutunu kullanabilirsiniz.

2. Uygulamayı başlatmak için:
   ```bash
   python trader.py
   ```

## .exe Olarak Derleme (PyInstaller)

1. PyInstaller'ı yükleyin:
   ```bash
   pip install pyinstaller
   ```
2. .exe oluşturmak için:
   ```bash
   pyinstaller --onefile --windowed trader.py
   ```
   - Çıktı dosyası `dist/trader.exe` içinde bulunur.

## Açık Kaynak Kullanım

- Kodun tamamı açık kaynaklıdır.
- İsteyen herkes kodu inceleyebilir, geliştirebilir ve kendi bilgisayarında çalıştırabilir.

## Notlar

- Binance API anahtarlarınız ve Telegram API bilgileriniz sadece kendi bilgisayarınızda, yerel olarak saklanır; hiçbir şekilde başka bir sunucuya veya üçüncü tarafa gönderilmez.
- Yine de anahtarlarınızı güvenli şekilde saklamaya özen gösteriniz.
- Windows dışı sistemlerde de çalışır, ancak .exe sadece Windows içindir.
