#include <stdlib.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>

#include <byteswap.h>

// Read Bytes From File And Then Reset Cursor Position
static int fread_and_reset(FILE *stream, unsigned char *buff, int size) {
    size = fread(buff, 1, size, stream);
    fseek(stream, -size, SEEK_CUR);
    return size;
}

// Copy File Contents
static void copy_file(FILE *input, FILE *output) {
    int c;
    while ((c = fgetc(input)) != EOF) {
        fputc(c, output);
    }
}

// Get File Size
static long int get_file_size(FILE *stream) {
    fseek(stream, 0, SEEK_END);
    long int size = ftell(stream);
    fseek(stream, 0, SEEK_SET);
    return size;
}

// Write Integer To File
static void write_int(FILE *stream, uint32_t x) {
#if __BYTE_ORDER__ == __ORDER_BIG_ENDIAN__
    // Integer Must Be Little-Endian
    x = __bswap_32(x);
#endif
    fwrite(&x, 4, 1, stream);
}

#define STORAGE_VERSION 3

#define INVALID_ARGS() fprintf(stderr, "Invalid Arguments\n"); exit(1);
int main(int argc, char *argv[]) {
    if (argc == 4) {
        int add_header;
        if (strcmp(argv[1], "add-header") == 0) {
            add_header = 1;
        } else if (strcmp(argv[1], "remove-header") == 0) {
            add_header = 0;
        } else {
            INVALID_ARGS();
        }

        FILE *input = fopen(argv[2], "rb");
        FILE *output = fopen(argv[3], "wb");
        if (input == NULL || output == NULL) {
            fprintf(stderr, "Unable To Open Input/Output File(s)\n");
            exit(1);
        }

        uint32_t first_byte = 0;
        int bytes_read = fread_and_reset(input, (unsigned char *) &first_byte, 4);
#if __BYTE_ORDER__ == __ORDER_BIG_ENDIAN__
        // Convert Little-Endian To Big-Endian
        first_byte = __bswap_32(first_byte);
#endif
        int input_has_header = bytes_read == 4 && first_byte == STORAGE_VERSION;

        if ((add_header && input_has_header) || (!add_header && !input_has_header)) {
            fprintf(stderr, add_header ? "Header Already Exists\n" : "Header Is Already Removed\n");

            copy_file(input, output);
        } else if (add_header) {
            fprintf(stderr, "Adding Header...\n");

            write_int(output, STORAGE_VERSION);
            uint32_t size = get_file_size(input);
            write_int(output, size);
            copy_file(input, output);
        } else {
            fprintf(stderr, "Removing Header...\n");

            fseek(input, 8, SEEK_CUR);
            copy_file(input, output);
        }

        fprintf(stderr, "Done\n");

        fclose(input);
        fclose(output);
    } else if (argc == 1) {
        fprintf(stderr, "HELP:\n    %s <add-header|remove-header> <input-file> <output-file>\n", argv[0]);
        exit(1);
    } else {
        INVALID_ARGS();
    }
}
