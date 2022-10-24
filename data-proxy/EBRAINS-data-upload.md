# Readme - EBRAINS-data-upload.py

EBRAINS-data-upload.py is a Python script that lets you upload data to your EBRAINS storage bucket directly from the command line, in order to prevent errors occurring in the browser when uploading large files or a large number of files. We have tested it for both data categories.

## How to use
 - Start the script from your command prompt or terminal/shell: ```python EBRAINS-data-upload.py```
 - You will be redirected to your browser for the EBRAINS login.
 - To obtain your EBRAINS authentication token, please start the Jupyter lab as prompted, and run the notebook. This will give you a button, please click it to copy your token to the clipboard. Then paste the token back into the Python window.
 - Follow the instructions to provide the bucket name, the folder to upload to, and the path to the data files.
 - The upload progress will be listed file by file. Please keep the window open until it is finished.
 - If for any reason the upload is interrupted, you can run it again and select to skip exising files, then it will continue where it left off.

## Please note

The script is set up in such a way that it takes all content in the data folder, and copies it to the EBRAINS storage without creating the parent folder itself (contents only). If you prefer to keep the top folder as well, you can specify the top folder name as the folder you wish to upload to (this will create a new folder if it didn't exist before).
