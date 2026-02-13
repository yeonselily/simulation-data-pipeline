#pragma once

#include <glad/glad.h>
#include <iostream>

// function declarations
void checkCompileErrors(GLuint shader, std::string type);

const char *VertexShader = 
"#version 450 core\n\
layout (location = 0) in vec3 aPos;\n\
layout (location = 1) in vec3 aColor;\n\
layout (location = 2) in vec2 aTexCoord;\n\
\n\
out vec3 ourColor;\n\
out vec2 TexCoord;\n\
\n\
void main()\n\
{\n\
    gl_Position = vec4(aPos, 1.0);\n\
    ourColor = aColor;\n\
    TexCoord = aTexCoord;\n\
}";

const char *FragmentShader =
"#version 450 core\n\
out vec4 FragColor;\n\
\n\
in vec3 ourColor;\n\
in vec2 TexCoord;\n\
\n\
uniform sampler2D ourTexture;\n\
\n\
void main()\n\
{\n\
    vec2 newTexCoord = TexCoord;\n\
    newTexCoord.y = 1.0 - newTexCoord.y;\n\
    FragColor = texture(ourTexture, newTexCoord);\n\
}";

// NewShader returns the program ID associated with the vertex/fragment shaders
// needed to render the simulation space RGB data to the quad.
unsigned int NewShader() {
    unsigned int vertex, fragment;

    // Compile vertex shader
    vertex = glCreateShader(GL_VERTEX_SHADER);
    glShaderSource(vertex, 1, &VertexShader, NULL);
    glCompileShader(vertex);
    checkCompileErrors(vertex, "VERTEX");

    // Compile fragment shader
    fragment = glCreateShader(GL_FRAGMENT_SHADER);
    glShaderSource(fragment, 1, &FragmentShader, NULL);
    glCompileShader(fragment);
    checkCompileErrors(fragment, "FRAGMENT");
    
    // Create shader program
    unsigned int ID = glCreateProgram();
    glAttachShader(ID, vertex);
    glAttachShader(ID, fragment);
    glLinkProgram(ID);
    checkCompileErrors(ID, "PROGRAM");
    
    // Delete shader data as the shader program is now linked.
    glDeleteShader(vertex);
    glDeleteShader(fragment);

    return ID;
}

// checkCompileErrors is a helper function used to check for errors when 
// compiling shaders, and print them out to stderr if any are encountered.
void checkCompileErrors(GLuint shader, std::string type) {
    GLint success;
    GLchar infoLog[1024];

    if (type == "PROGRAM") {
        glGetProgramiv(shader, GL_LINK_STATUS, &success);
        if(!success) {
            glGetProgramInfoLog(shader, 1024, NULL, infoLog);
            std::cerr << "[ERROR] PROGRAM_LINKING_ERROR of type: " << type << std::endl << infoLog << std::endl;
        }

        return;
    }

    glGetShaderiv(shader, GL_COMPILE_STATUS, &success);
    if(!success) {
        glGetShaderInfoLog(shader, 1024, NULL, infoLog);
        std::cerr << "[ERROR] SHADER_COMPILATION_ERROR of type: " << type << std::endl << infoLog << std::endl;
    }

    return;
}
