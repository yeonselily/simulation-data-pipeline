#pragma once

#include <iostream>
#include <fstream>

namespace simviz {
    const uint32_t FileSignature = 0xcc10adde;
    const size_t FileSignatureBitWidth = 4;
    const size_t SimulationWidthBitWidth = 8;
    const size_t SimulationHeightBitWidth = 8;
    const size_t RGBDataOffset = FileSignatureBitWidth + SimulationWidthBitWidth + SimulationHeightBitWidth;
    const size_t NumRGBBytes = 3;

    class RGBFile {
        private:
            const int x;
            const int y;

            std::ofstream fs;

        public:
            RGBFile(const int width, const int height);
            RGBFile(const char* fpath, const int width, const int height);
            ~RGBFile();
            void open(const char* fpath);
            void write(const char* data, int n);
            void close();
    };
};
