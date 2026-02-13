// GLAD and GLFW. GLAD loads the OpenGL functions/extensions,
// and GLFW is the windowing library.
#include <glad/glad.h>
#include <GLFW/glfw3.h>

// Helper for loading/compiling the vertex/fragment shaders.
#include "simviz.h"
#include "./shader.h"

// C++ deps
#include <iostream>
#include <fstream>
#include <string>
#include <sstream>
#include <vector>
#include <chrono>
#include <thread>
#include <limits>

// Function declarations
void glfwErrorCallback(int error, const char *description);
void keyCallback(GLFWwindow* window, int key, int scancode, int action, int mods);

const unsigned int ScreenWidth = 1024;
const unsigned int ScreenHeight = 768;

// ### Global variables ###
// simStep is the current simulation step.
int simStep = 0;

// maxStep is the maximum number of steps in the simulation.
// The simulation data is streamed in so we don't know this 
// value until we reach the end of the file. So we set it 
// initially as MAX_INT.
int maxStep = std::numeric_limits<int>::max();

// pause indicates whether the simulation has been paused.
bool pause = false;

int main(int argc, char **argv) {
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <path/to/sim-file>" << std::endl;

        return 1;
    }
    
    // Open the file
    std::ifstream fd(argv[1], std::ios::binary);
    if (fd.fail()) {
        std::cerr << "[ERROR] Failed to open file: " << argv[1] << std::endl;

        return 1;
    }

    // Check file signature
    uint32_t fileSig = 0;
    fd.read(static_cast<char*>(static_cast<void*>(&fileSig)), simviz::FileSignatureBitWidth);
    if (simviz::FileSignature ^ fileSig) {
        std::cerr << "[ERROR]  Invalid file type." << std::endl;

        return 1;
    }

    // Read in the simulation space width and height.
    uint64_t simWidth = 0;
    uint64_t simHeight = 0;
    fd.read(static_cast<char*>(static_cast<void*>(&simWidth)), simviz::SimulationWidthBitWidth);
    fd.read(static_cast<char*>(static_cast<void*>(&simHeight)), simviz::SimulationHeightBitWidth);

    std::cout << "[INFO] Rendering simulation space of [" << simWidth << ", " << simHeight << "]" << std::endl;

    // Allocate memory for simulation RGB data.
    int simSpaceSize = simWidth * simHeight * simviz::NumRGBBytes;
    unsigned char *simulationRGBData = new unsigned char[simSpaceSize];

    

    // Initialize and create GLFW Window.
    glfwInit();
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 4);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 5);
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);
    glfwSetErrorCallback(glfwErrorCallback);
    GLFWwindow* window = glfwCreateWindow(ScreenWidth, ScreenHeight, "SimViz", NULL, NULL);
    if (window == NULL)
    {
        std::cerr << "[ERROR] Failed to initialize or create GLFW window" << std::endl;
        glfwTerminate();

        return -1;
    }
    glfwMakeContextCurrent(window);
    glfwSetKeyCallback(window, keyCallback);
    
    // Load OpenGL Function Pointers
    if (!gladLoadGLLoader((GLADloadproc)glfwGetProcAddress))
    {
        std::cerr << "[ERROR] Failed to load OpenGL function pointers using GLAD" << std::endl;

        return -1;
    }
    
    // Compile and load vertex and fragment shaders.
    unsigned int programID = NewShader();

    // Create vertex data and associated buffers for the quad we will be
    // rendering the texture to.
    // ------------------------------------------------------------------
    float vertices[] = {
        // positions          // colors           // texture coords
         1.0f,  1.0f, 0.0f,   1.0f, 0.0f, 0.0f,   1.0f, 1.0f, // top right
         1.0f, -1.0f, 0.0f,   0.0f, 1.0f, 0.0f,   1.0f, 0.0f, // bottom right
        -1.0f, -1.0f, 0.0f,   0.0f, 0.0f, 1.0f,   0.0f, 0.0f, // bottom left
        -1.0f,  1.0f, 0.0f,   1.0f, 1.0f, 0.0f,   0.0f, 1.0f  // top left 
    };
    unsigned int indices[] = {
        0, 1, 3, // first triangle
        1, 2, 3  // second triangle
    };
    unsigned int VAO, VBO, EBO;
    glGenVertexArrays(1, &VAO);
    glGenBuffers(1, &VBO);
    glGenBuffers(1, &EBO);

    glBindVertexArray(VAO);

    glBindBuffer(GL_ARRAY_BUFFER, VBO);
    glBufferData(GL_ARRAY_BUFFER, sizeof(vertices), vertices, GL_STATIC_DRAW);

    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO);
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, sizeof(indices), indices, GL_STATIC_DRAW);

    // position attribute
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 8 * sizeof(float), (void*)0);
    glEnableVertexAttribArray(0);

    // color attribute
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 8 * sizeof(float), (void*)(3 * sizeof(float)));
    glEnableVertexAttribArray(1);

    // texture coord attribute
    glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 8 * sizeof(float), (void*)(6 * sizeof(float)));
    glEnableVertexAttribArray(2);


    // Create and load the texture object.
    unsigned int texture;
    glGenTextures(1, &texture);
    glBindTexture(GL_TEXTURE_2D, texture); 
     
     // Set wrapping parameters
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER );
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER );
    float borderColor[] = {1.0f, 1.0f, 0.0f, 1.0f};
    glTexParameterfv(GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, borderColor);

    // Set texture filtering parameters
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);

    // Set Pixel Alignment
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1);
    
    // Set shader
    glUseProgram(programID);
    glUniform1i(glGetUniformLocation(programID, "texture"), 0);

    // Read in first set of RGB data from the simulation.
    fd.read((char*)simulationRGBData, simSpaceSize);
    if (fd.fail()) { 
        std::cerr << "[ERROR] Failed to read in simulation data." << std::endl;

        return 1;
    }

    // Begin render loop
    int lastSimStep = simStep;
    while (!glfwWindowShouldClose(window))
    {
        // If not paused, progress simulation at a rate of 5 FPS.
        if (!pause) {
            std::this_thread::sleep_for(std::chrono::milliseconds(200));
        }

        // Set title based on state.
        std::string title = "SimViz - Step: " + std::to_string(simStep);
        if (simStep == maxStep) {
            title += " (end)";
        }
        
        if (pause) {
            title += " (paused)";
        }
        glfwSetWindowTitle(window, title.c_str());
        
        // Begin rendering frame.
        glClearColor(0.2f, 0.3f, 0.3f, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT);

        // Bind texture
        glActiveTexture(GL_TEXTURE0);
        glBindTexture(GL_TEXTURE_2D, texture);

        // Copy in texture data as the RGB data from the simulation file.
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, simWidth, simHeight, 0, GL_RGB, GL_UNSIGNED_BYTE, simulationRGBData);
        glGenerateMipmap(GL_TEXTURE_2D);

        // Render quad with texture
        glUseProgram(programID);
        glBindVertexArray(VAO);
        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, 0);

        glfwSwapBuffers(window);
        glfwPollEvents();

        // Read in next frame of data
        if (!pause && simStep < maxStep) {
            simStep++;
        }

        if (simStep == lastSimStep) {
            continue;
        }
        
        // If paused, seek to selected step.
        if (pause) {
            // clear state incase of prior fail
            fd.clear();
            int offset = simStep * simSpaceSize + simviz::RGBDataOffset;
            fd.seekg(offset, std::ios_base::beg);
        }
        
        // If we aren't at the end of the file, read in next sim step.
        if (!fd.eof()) {
            fd.read((char*)simulationRGBData, simSpaceSize);
            // If we are the end of the file, pause sim, and set 
            // appropriate step.
            if (fd.eof()) {
                pause = true;
                simStep--;
                maxStep = simStep;
            }

            lastSimStep = simStep;
        } 
    }

    // Deallocate all resources.
    glDeleteVertexArrays(1, &VAO);
    glDeleteBuffers(1, &VBO);
    glDeleteBuffers(1, &EBO);
    free(simulationRGBData);
    fd.close();
    glfwTerminate();

    return 0;
}

// glfwErrorCallback is called when GLFW encounters an error. The provided
// error and description are then streamed into stderr.
void glfwErrorCallback(int error, const char *description)
{
   std::cerr << "[GLFW ERROR] " << error << ": " << description << std::endl;
}

// keyCallback is called by GLFW for processing key inputs.
void keyCallback(GLFWwindow* window, int key, int scancode, int action, int mods) {
    if (action != GLFW_PRESS) {
        return;
    }

    switch (key) {
        case GLFW_KEY_SPACE:
            pause = !pause;
            break;
        case GLFW_KEY_RIGHT:
            if (!pause || simStep >= maxStep) { break; }
            simStep++;
            break;
        case GLFW_KEY_LEFT:
            if (!pause || simStep <= 0) { break; }
            simStep--;
            break;
    }

    return;
}
