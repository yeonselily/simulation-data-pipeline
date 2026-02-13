#include <iostream>

// Boost APIs
#include <boost/program_options.hpp>
#include <boost/log/core.hpp>
#include <boost/log/trivial.hpp>
#include <boost/log/expressions.hpp>

#include <mass/Mass.h>
#include <mass/Logger.h>

#include <simviz.h>

#include "Heat2D.h"

namespace po = boost::program_options;
namespace logging = boost::log;

int main(int argc, char* argv[]) {

	// setup and parse program options
	po::options_description desc("options");
	desc.add_options()
		("help", "print help message")
		("verbose", po::bool_switch()->default_value(false), "set verbose output")
		("size", po::value<int>()->default_value(100), "size of simulation space")
		("heat_time", po::value<int>()->default_value(2700), "simulation heat time")
		("max_time", po::value<int>()->default_value(3000), "max simulation time steps")
		("interval", po::value<int>()->default_value(0), "output interval")
		("out_file", po::value<std::string>()->default_value("./heat2d.viz"), "SimViz file output (requires \"mass-cuda\" mode)")
	;

	po::variables_map vm;
	po::store(po::parse_command_line(argc, argv, desc), vm);
	po::notify(vm);

	if (vm.count("help")) {
		std::cout << desc << std::endl;

		return 0;
	}

	// Setup logger
	logging::trivial::severity_level log_level = logging::trivial::info;
	if (vm["verbose"].as<bool>()) {
		log_level = logging::trivial::debug;
	}

	mass::logger::setLogLevel(log_level);

	// Get simulation attributes
	int size = vm["size"].as<int>();
	int heat_time = vm["heat_time"].as<int>();
	int max_time = vm["max_time"].as<int>();
	int interval = vm["interval"].as<int>();

	// Create simviz file if interval is non-zero.
	simviz::RGBFile vizFile(size, size);
	if (interval > 0) {
		vizFile.open(vm["out_file"].as<std::string>().c_str());
	}

	mass::logger::info(
		"Running Heat2D with params: size=%d, heat_time=%d, max_time=%d, interval=%d",
		size, heat_time, max_time, interval
	);

	Heat2D heat;
	heat.runMassSim(size, max_time, heat_time, interval, vizFile);

	vizFile.close();

	return 0;
}
