from Assembler import Assemble
from Ingestor import Ingestor

def main():
    # Run the ingestion process to populate the database
    Ingestor.ingest_all()

    # Run the assembly process to create programme files
    Assemble.assemble()

    # Clean up files older than 2 days
    Assemble.cleanup(2)


if __name__ == '__main__':
    main()