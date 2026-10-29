"""A user-operated local audio chooser owned by the instrument window."""
import os


def pick_audio_file(owner=None):
    if os.name=='nt':
        import ctypes
        from ctypes import wintypes as w

        class OpenFileName(ctypes.Structure):
            _fields_=[('lStructSize',w.DWORD),('hwndOwner',w.HWND),('hInstance',w.HINSTANCE),
                      ('lpstrFilter',w.LPCWSTR),('lpstrCustomFilter',w.LPWSTR),('nMaxCustFilter',w.DWORD),
                      ('nFilterIndex',w.DWORD),('lpstrFile',w.LPWSTR),('nMaxFile',w.DWORD),
                      ('lpstrFileTitle',w.LPWSTR),('nMaxFileTitle',w.DWORD),('lpstrInitialDir',w.LPCWSTR),
                      ('lpstrTitle',w.LPCWSTR),('Flags',w.DWORD),('nFileOffset',w.WORD),
                      ('nFileExtension',w.WORD),('lpstrDefExt',w.LPCWSTR),('lCustData',ctypes.c_ssize_t),
                      ('lpfnHook',ctypes.c_void_p),('lpTemplateName',w.LPCWSTR),('pvReserved',ctypes.c_void_p),
                      ('dwReserved',w.DWORD),('FlagsEx',w.DWORD)]

        buffer=ctypes.create_unicode_buffer(32768)
        dialog=OpenFileName()
        dialog.lStructSize=ctypes.sizeof(dialog);dialog.hwndOwner=owner
        dialog.lpstrFilter='音乐文件\0*.mp3;*.wav;*.ogg;*.flac\0所有文件\0*.*\0\0'
        dialog.nFilterIndex=1;dialog.lpstrFile=ctypes.cast(buffer,w.LPWSTR);dialog.nMaxFile=len(buffer)
        dialog.lpstrTitle='导入一首音乐';dialog.Flags=0x80000|0x1000|0x800|0x8
        api=ctypes.WinDLL('comdlg32',use_last_error=True)
        api.GetOpenFileNameW.argtypes=[ctypes.POINTER(OpenFileName)];api.GetOpenFileNameW.restype=w.BOOL
        if api.GetOpenFileNameW(ctypes.byref(dialog)):return buffer.value
        api.CommDlgExtendedError.restype=w.DWORD
        if api.CommDlgExtendedError():raise OSError('Cannot open the audio file chooser; drop a file into the window instead')
        return None

    import tkinter as tk
    from tkinter import filedialog
    root=tk.Tk();root.withdraw()
    try:
        return filedialog.askopenfilename(title='导入一首音乐',filetypes=[('Audio','*.mp3 *.wav *.ogg *.flac')]) or None
    finally:root.destroy()
