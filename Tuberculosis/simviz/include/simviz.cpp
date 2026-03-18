#include <simviz.h>

using namespace simviz;

// RGBFile consctructor that doesn't initialize the file stream.
RGBFile::RGBFile(const int width, const int height) : x(width), y(height) { }

// RGBFile constructor creates an RGB file stream and writes the appropriate
// header data to it.
RGBFile::RGBFile(const char* fpath, const int width, const int height)
    : x(width), y(height) {
    open(fpath);
    
    return;
}

// RGBFile Destructor just makes sure we close the handle to the RGB file.
RGBFile::~RGBFile() {
    if (!fs) {
        return; 
    }

    fs.close();
}

void RGBFile::open(const char* fpath) {
    // Open file
    fs = std::ofstream(fpath, std::ios::binary | std::ios::out);
    if (fs.fail()) {
        std::cerr << "[ERROR] Failed to open file: " << fpath << std::endl;

        return;
    }

    // Write file signature
    uint32_t fileSig = FileSignature;
    fs.write(static_cast<char*>(static_cast<void*>(&fileSig)), FileSignatureBitWidth);

    // Write simulation space size
    uint64_t simWidth = x;
    uint64_t simHeight = y;
    fs.write(static_cast<char*>(static_cast<void*>(&simWidth)), SimulationWidthBitWidth);
    fs.write(static_cast<char*>(static_cast<void*>(&simHeight)), SimulationHeightBitWidth);

    if (fs.fail()) {
        std::cerr << "[ERROR] Failed to write to file: " << fpath << std::endl;
    }

    return;
}

// write writes the provided data to the RGB file. Validation checks are not
// performed. If what's written is not RGB_8 data, then it may not work as
// expected with the visualization app.
void RGBFile::write(const char* data, int n) {
    if (!fs) {
        return;
    }

    fs.write(data, n);
}

// close simply closes the underlying file stream.
void RGBFile::close() {
    if (!fs) {
        return; 
    }

    fs.close();
}
