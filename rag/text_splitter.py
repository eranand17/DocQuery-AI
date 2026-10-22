from langchain_text_splitters import RecursiveCharacterTextSplitter
def split_text_into_chunks(pages, chunk_size=1000, chunk_overlap=200):
    """
    Splits the input text into smaller chunks.

    Args:
        pages (list): A list of dictionaries containing page numbers and text.
        chunk_size (int): The maximum size of each chunk.
        chunk_overlap (int): The number of overlapping characters between chunks.

    Returns:
        list: A list of text chunks.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunks =[]
    for page in pages:
        page_chunks = text_splitter.split_text(page["text"])
        for chunk in page_chunks:
            chunks.append({
                "page": page["page"],
                "text": chunk
            })
    return chunks