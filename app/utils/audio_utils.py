import wave
from typing import List

def merge_wav_files(input_files: List[str], output_file: str):
    data = []
    for infile in input_files:
        with wave.open(infile, 'rb') as w:
            data.append([w.getparams(), w.readframes(w.getnframes())])
    output = wave.open(output_file, 'wb')
    output.setparams(data[0][0])
    for params, frames in data:
        output.writeframes(frames)
    output.close() 