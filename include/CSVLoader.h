#pragma once

#include "States.h"

#include <vector>
#include <string>

class CSVLoader
{
public:

    static TerrainData loadTerrain(
        const std::string& height_file,
        const std::string& type_file
    );

    static std::vector<SensorSite> loadSensors(
        const std::string& filename
    );

    static EnvState loadEnvironment(
        const std::string& filename
    );

    static std::vector<NFZTriangle> loadNFZ(
    const std::string& filename
    );

};