from file_processor import FileProcessor


def test_split_text_into_segments_respects_max_length():
    processor = FileProcessor(segment_size=50)
    text = (
        "第一段内容比较短。\n\n"
        "第二段内容也比较短。\n\n"
        "第三段内容依然比较短。"
    )

    segments = processor.split_text_into_segments(text, max_length=30)

    assert segments
    assert all(len(segment) <= 30 for segment in segments)


def test_detect_language_basic_cases():
    processor = FileProcessor()

    assert processor.detect_language("这是一段中文文本。") == "zh"
    assert processor.detect_language("This is an English sentence.") == "en"
