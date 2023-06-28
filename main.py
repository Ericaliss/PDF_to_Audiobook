import PyPDF3 # pip install PyPDF3
import pyttsx3 # pip install pyttsx3
import pdfplumber # pip install pdfplumber
import glob
import os
from pydub import AudioSegment # pip install pydub
from mutagen.id3 import ID3, TIT2, TALB # pip install mutagen
from typing import Dict
import fitz  # pip install pymupdf
import re
import shutil

def remove_invalid_chars(string):
    # Define a regular expression pattern for characters not allowed in Windows paths
    pattern = r'[<>:"/\\|?*\r]'
    
    # Remove invalid characters from the string
    sanitized_string = re.sub(pattern, '', string)
    
    return sanitized_string

def compress_mp3(input_file, output_file, bitrate='64k'):
    audio = AudioSegment.from_file(input_file)
    audio.export(output_file, format='mp3', bitrate=bitrate)
    
def add_metadata(mp3_file, title, album):
    # Load the MP3 file
    audio = ID3(mp3_file)

    # Create the title, album, and track number tags
    audio["TIT2"] = TIT2(encoding=3, text=title)
    audio["TALB"] = TALB(encoding=3, text=album)

    # Save the changes
    audio.save()
    
def get_bookmarks(filepath):
    
    with fitz.open(filepath) as doc:
        filename = os.path.splitext(os.path.basename(filepath))[0]
        toc = doc.get_toc()
        count = 0
        toc =  [x for x in toc if x[0] == 1]
        if(len(toc) < 1 ):
            shutil.copy(filepath,'pdf/split/'+filename+'.pdf')
        else:  
            for bookmark in toc:
        
                title = bookmark[1]
                page_number = bookmark[2]
                
                if(count < len(toc)-1):
                    next_page = toc[count+1][2]
                else:
                    next_page = len(doc)
                    
                #print(f"Title: {title}, Page: {page_number}")
                new_doc = fitz.open()
                new_doc.insert_pdf(doc, from_page=page_number-1, to_page=next_page-1)
                new_doc.save('pdf/split/'+filename+'_'+remove_invalid_chars(title)+'.pdf')
            
                count = count + 1   
def generate_structure():
    folders = {'pdf','pdf/split','audio','audio/compressed'}
    for folder in folders:
        os.makedirs('folder', exist_ok=True)

def main():
    
    generate_structure()
         
    pdf_files = glob.glob('pdf/*.pdf')
    # splitting bookmarks        
    for file in pdf_files:
        try:
            get_bookmarks(file) 
        except Exception as e:
            print("Cannot split bookmarks : "+ file + f'{e}')
            
    
    pdf_files = glob.glob('pdf/split/*.pdf')
    # Generate the Audio  
    for file in pdf_files:
        try:
            book = open(file, 'rb')
            pdfReader = PyPDF3.PdfFileReader(book)
            # Extracting text
            pages = pdfReader.numPages
            filename = os.path.splitext(os.path.basename(file))[0]
            print(filename)
            finalText = ""
            with pdfplumber.open(file) as pdf:
                for i in range(0, pages): 
                    page = pdf.pages[i]
                    text = page.extract_text()
                    finalText += text
                    print("Extracting text "+ str(i+1) +"/"+str(pages))
            
            book.close()
            os.remove(file)
        except Exception as e:
            print("Cannot extract text : "+ file + f'{e}')
        # Generate Audio
        
        try:
            input_filename = 'audio/'+filename+'.mp3'
            output_filename = 'audio/compressed/'+filename+'.mp3'
    
            print('Generate : '+input_filename)
            engine = pyttsx3.init()
            engine.save_to_file(finalText, input_filename)
            engine.runAndWait()
        except Exception as e:
            print("Cannot generate audio : "+ file + f'{e}')
            
        try:
            print('Compressing to 64k : '+input_filename)
            compress_mp3(input_filename, output_filename, bitrate='64k')
            os.remove(input_filename)
        except Exception as e:
            print("Cannot compress : "+ file + f'{e}')
        try:
            print('Add metadata to : '+output_filename)
            split = filename.split('_')
            add_metadata(output_filename,split[1],split[0])
            print('\n')
        except Exception as e:
            print("Cannot add metadata : "+ file + f'{e}')
         
    
if __name__ == "__main__":
   main()