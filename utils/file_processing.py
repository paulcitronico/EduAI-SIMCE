import os
import tempfile
import subprocess
import platform

def convertir_pptx_a_pdf(ruta_entrada, ruta_salida):
    try:
        sistema = platform.system()
        
        if sistema == 'Windows':
            try:
                import win32com.client
                powerpoint = win32com.client.Dispatch("PowerPoint.Application")
                deck = powerpoint.Presentations.Open(ruta_entrada)
                deck.SaveAs(ruta_salida, 32)
                deck.Close()
                powerpoint.Quit()
                return True
            except:
                pass
        
        temp_dir = tempfile.mkdtemp()
        temp_salida = os.path.join(temp_dir, "temp.pdf")
        
        comando = [
            'libreoffice', '--headless', '--convert-to', 'pdf', 
            '--outdir', temp_dir, ruta_entrada
        ]
        
        subprocess.run(comando, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if os.path.exists(temp_salida):
            os.rename(temp_salida, ruta_salida)
            return True
        
        return False
    except Exception as e:
        print(f"Error al convertir PPTX a PDF: {str(e)}")
        return False

def extraer_id_youtube(url):
    import re
    patrones = [
        r'(?:youtube\.com\/watch\?v=|\/v\/|youtu\.be\/)([^&]+)',
        r'(?:youtube\.com\/embed\/)([^&]+)',
        r'(?:youtube\.com\/v\/)([^&]+)'
    ]
    
    for patron in patrones:
        match = re.search(patron, url)
        if match:
            return match.group(1)
    return None