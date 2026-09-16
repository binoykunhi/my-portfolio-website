import jiwer

consensus = "This is a test sentence."
transcript = "This is a test sentence."

transformation = jiwer.Compose([
    jiwer.ToLowerCase(),
    jiwer.RemovePunctuation(),
    jiwer.RemoveMultipleSpaces(),
    jiwer.Strip(),
    jiwer.ExpandCommonEnglishContractions(),
    lambda x: [sentence.split() for sentence in x]
])

try:
    wer = jiwer.wer(
        consensus, 
        transcript, 
        reference_transform=transformation, 
        hypothesis_transform=transformation
    )
    print(f"WER: {wer}")
except Exception as e:
    print(f"Error: {e}")
