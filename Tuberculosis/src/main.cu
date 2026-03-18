#include <iostream>

// Boost APIs
#include <boost/program_options.hpp>
#include <boost/log/core.hpp>
#include <boost/log/trivial.hpp>
#include <boost/log/expressions.hpp>

#include <simviz.h>

#include <mass/Mass.h>
#include <mass/Logger.h>

#include "Tuberculosis.h"
#include "Timer.h"

namespace po = boost::program_options;
namespace logging = boost::log;

int main(int argc, char* argv[]) {
	// Setup and parse program options.
	po::options_description desc("general options");
	desc.add_options()
		("help", "print help message")
		("verbose", po::bool_switch()->default_value(false), "set verbose output")
		("interval", po::value<int>()->default_value(1), "output interval")
		("out_file", po::value<std::string>()->default_value("./tuberculosis.viz"), "SimViz file output")
	;

	po::options_description sim_opts("simulation options");
	sim_opts.add_options()
		("seed", po::value<int>()->default_value(1), "seed used for RNG. if left unset, current time is used") // TEST changed from -1 to 1
		("size", po::value<int>()->default_value(40), "size of simulation space")
		("total_days", po::value<int>()->default_value(100), "max simulation time steps")
		("init_macro_num", po::value<int>()->default_value(100), "initial number of macrophages")
	;
	desc.add(sim_opts);

	po::variables_map vm;
	po::store(po::parse_command_line(argc, argv, desc), vm);
	po::notify(vm);

	if (vm.count("help")) {
		std::cout << desc << std::endl;

		return 0;
	}

	// Setup logger.
	logging::trivial::severity_level log_level = logging::trivial::info;
	if (vm["verbose"].as<bool>()) {
		log_level = logging::trivial::debug;
	}

	mass::logger::setLogLevel(log_level);

	// Parse simulation options and get a config struct.
	tuberculosis::ConfigOpts opts = tuberculosis::parseSimConfig(vm);

	int interval = vm["interval"].as<int>();
	mass::logger::info(
		"Running Tuberculosis with params: size=%d, total_days=%d, init_macro_num=%d, interval=%d",
		opts.size, opts.total_days, opts.init_macro_num, interval
	);

	// Create viz file if interval is non-zero.
	simviz::RGBFile vizFile(opts.size * 2, opts.size * 2);
	if (interval > 0) {
		vizFile.open(vm["out_file"].as<std::string>().c_str());
	}

	Timer timer;
	timer.start();

    // Run application
	tuberculosis::runSimulation(opts, interval, vizFile);

	mass::logger::info("Total execution time %dus\n", timer.lap());
    
	vizFile.close();

	return 0;
}