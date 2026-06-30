#include "G4Box.hh"
#include "G4Element.hh"
#include "G4Event.hh"
#include "G4EventManager.hh"
#include "G4Isotope.hh"
#include "G4LogicalVolume.hh"
#include "G4Material.hh"
#include "G4NistManager.hh"
#include "G4PVPlacement.hh"
#include "G4ParticleDefinition.hh"
#include "G4ParticleGun.hh"
#include "G4ParticleTable.hh"
#include "G4PhysListFactory.hh"
#include "G4Run.hh"
#include "G4RunManager.hh"
#include "G4Step.hh"
#include "G4SystemOfUnits.hh"
#include "G4ThreeVector.hh"
#include "G4Track.hh"
#include "G4TransportationManager.hh"
#include "G4Tubs.hh"
#include "G4Types.hh"
#include "G4UserEventAction.hh"
#include "G4UserRunAction.hh"
#include "G4UserSteppingAction.hh"
#include "G4VProcess.hh"
#include "G4VModularPhysicsList.hh"
#include "G4VUserActionInitialization.hh"
#include "G4VUserDetectorConstruction.hh"
#include "G4VUserPrimaryGeneratorAction.hh"
#include "Randomize.hh"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <vector>

namespace fs = std::filesystem;

struct Config {
  double energyMeV = 5.0;
  double thicknessCm = 1.0;
  int events = 10000;
  double liRadiusCm = 2.0;
  double liDensityGcm3 = 0.534;
  double sourceToLiFrontCm = 1.0;
  double detectorDistanceCm = 10.0;
  double timeBinPs = 1.0;
  long seed = 20260701;
  std::string physicsList = "QGSP_BIC_HP";
  std::string outDir = "runs/geant4/stage0_debug";
};

struct GeometryState {
  double sourceZ = 0.0;
  double liFrontZ = 0.0;
  double liRearZ = 0.0;
  double detectorZ = 0.0;
};

class Tally {
 public:
  explicit Tally(const Config& cfg) : cfg_(cfg) {}

  void AddBirth(double timePs, double weight) {
    birthWeight_ += weight;
    birthCount_ += 1;
    AddToHist(birthHist_, timePs, weight);
  }

  void AddExit(double timePs, double weight) {
    exitWeight_ += weight;
    exitCount_ += 1;
    AddToHist(exitHist_, timePs, weight);
  }

  void AddDetector(double timePs, double weight) {
    detectorWeight_ += weight;
    detectorCount_ += 1;
    AddToHist(detectorHist_, timePs, weight);
  }

  void AddPrimaryLiEntry() { primaryLiEntryCount_ += 1; }

  void AddLiProcess(const std::string& processName) {
    liProcessCounts_[processName] += 1;
  }

  void AddLiSecondary(const std::string& particleName) {
    liSecondaryCounts_[particleName] += 1;
  }

  void Write(const GeometryState& geom) const {
    fs::create_directories(cfg_.outDir);
    WriteHist(fs::path(cfg_.outDir) / "birth_neutron_time_hist.csv", birthHist_);
    WriteHist(fs::path(cfg_.outDir) / "exit_neutron_time_hist.csv", exitHist_);
    WriteHist(fs::path(cfg_.outDir) / "detector_neutron_time_hist.csv", detectorHist_);

    const double exitRelErr = exitCount_ > 0 ? 1.0 / std::sqrt(static_cast<double>(exitCount_)) : 0.0;
    const double detRelErr = detectorCount_ > 0 ? 1.0 / std::sqrt(static_cast<double>(detectorCount_)) : 0.0;

    std::ofstream out(fs::path(cfg_.outDir) / "summary.json");
    out << std::setprecision(12);
    out << "{\n";
    out << "  \"proton_energy_MeV\": " << cfg_.energyMeV << ",\n";
    out << "  \"D_Li_cm\": " << cfg_.thicknessCm << ",\n";
    out << "  \"N_primary\": " << cfg_.events << ",\n";
    out << "  \"physics_list\": \"" << cfg_.physicsList << "\",\n";
    out << "  \"li_material\": \"pure_7Li\",\n";
    out << "  \"li_density_g_cm3\": " << cfg_.liDensityGcm3 << ",\n";
    out << "  \"li_radius_cm\": " << cfg_.liRadiusCm << ",\n";
    out << "  \"source_to_li_front_cm\": " << cfg_.sourceToLiFrontCm << ",\n";
    out << "  \"detector_distance_behind_li_cm\": " << cfg_.detectorDistanceCm << ",\n";
    out << "  \"source_z_cm\": " << geom.sourceZ / cm << ",\n";
    out << "  \"li_front_z_cm\": " << geom.liFrontZ / cm << ",\n";
    out << "  \"li_rear_z_cm\": " << geom.liRearZ / cm << ",\n";
    out << "  \"detector_z_cm\": " << geom.detectorZ / cm << ",\n";
    out << "  \"birth_neutron_count\": " << birthCount_ << ",\n";
    out << "  \"birth_neutron_weight\": " << birthWeight_ << ",\n";
    out << "  \"Y_n_exit\": " << exitWeight_ << ",\n";
    out << "  \"Y_n_exit_per_primary\": " << exitWeight_ / static_cast<double>(cfg_.events) << ",\n";
    out << "  \"exit_neutron_count\": " << exitCount_ << ",\n";
    out << "  \"exit_relative_error_approx\": " << exitRelErr << ",\n";
    out << "  \"Y_n_detector_10cm\": " << detectorWeight_ << ",\n";
    out << "  \"Y_n_detector_10cm_per_primary\": "
        << detectorWeight_ / static_cast<double>(cfg_.events) << ",\n";
    out << "  \"detector_neutron_count\": " << detectorCount_ << ",\n";
    out << "  \"detector_relative_error_approx\": " << detRelErr << ",\n";
    out << "  \"time_bin_ps\": " << cfg_.timeBinPs << ",\n";
    out << "  \"primary_li_entry_count\": " << primaryLiEntryCount_ << ",\n";
    WriteStringCountMap(out, "li_process_counts", liProcessCounts_);
    out << ",\n";
    WriteStringCountMap(out, "li_secondary_counts", liSecondaryCounts_);
    out << "\n";
    out << "}\n";
  }

 private:
  void AddToHist(std::map<long long, double>& hist, double timePs, double weight) {
    const auto bin = static_cast<long long>(std::floor(timePs / cfg_.timeBinPs));
    hist[bin] += weight;
  }

  void WriteHist(const fs::path& path, const std::map<long long, double>& hist) const {
    std::ofstream out(path);
    out << "time_ps,count\n";
    for (const auto& [bin, count] : hist) {
      const double center = (static_cast<double>(bin) + 0.5) * cfg_.timeBinPs;
      out << std::setprecision(12) << center << "," << count << "\n";
    }
  }

  void WriteStringCountMap(
      std::ofstream& out,
      const std::string& key,
      const std::map<std::string, long long>& counts) const {
    out << "  \"" << key << "\": {";
    if (!counts.empty()) {
      out << "\n";
      size_t index = 0;
      for (const auto& [name, count] : counts) {
        out << "    \"" << name << "\": " << count;
        if (++index < counts.size()) {
          out << ",";
        }
        out << "\n";
      }
      out << "  ";
    }
    out << "}";
  }

  const Config& cfg_;
  long long primaryLiEntryCount_ = 0;
  long long birthCount_ = 0;
  long long exitCount_ = 0;
  long long detectorCount_ = 0;
  double birthWeight_ = 0.0;
  double exitWeight_ = 0.0;
  double detectorWeight_ = 0.0;
  std::map<long long, double> birthHist_;
  std::map<long long, double> exitHist_;
  std::map<long long, double> detectorHist_;
  std::map<std::string, long long> liProcessCounts_;
  std::map<std::string, long long> liSecondaryCounts_;
};

class DetectorConstruction final : public G4VUserDetectorConstruction {
 public:
  DetectorConstruction(const Config& cfg, GeometryState& geom) : cfg_(cfg), geom_(geom) {}

  G4VPhysicalVolume* Construct() override {
    auto* nist = G4NistManager::Instance();
    auto* vacuum = nist->FindOrBuildMaterial("G4_Galactic");

    auto* li7 = new G4Isotope("Li7", 3, 7, 7.016003 * g / mole);
    auto* liElement = new G4Element("Lithium7", "Li7", 1);
    liElement->AddIsotope(li7, 100.0 * perCent);
    auto* liMaterial = new G4Material(
        "pure_7Li", cfg_.liDensityGcm3 * g / cm3, 1, kStateSolid);
    liMaterial->AddElement(liElement, 1.0);

    geom_.sourceZ = -8.0 * cm;
    geom_.liFrontZ = geom_.sourceZ + cfg_.sourceToLiFrontCm * cm;
    geom_.liRearZ = geom_.liFrontZ + cfg_.thicknessCm * cm;
    geom_.detectorZ = geom_.liRearZ + cfg_.detectorDistanceCm * cm;

    const double worldHalfZ = std::max(std::abs(geom_.sourceZ), std::abs(geom_.detectorZ)) + 5.0 * cm;
    const double worldHalfXY = std::max(5.0 * cm, cfg_.liRadiusCm * cm + 2.0 * cm);

    auto* worldSolid = new G4Box("World", worldHalfXY, worldHalfXY, worldHalfZ);
    auto* worldLogic = new G4LogicalVolume(worldSolid, vacuum, "World");
    auto* worldPhys = new G4PVPlacement(
        nullptr, G4ThreeVector(), worldLogic, "World", nullptr, false, 0, true);

    auto* liSolid = new G4Tubs(
        "LiConverter", 0.0, cfg_.liRadiusCm * cm, 0.5 * cfg_.thicknessCm * cm, 0.0, 360.0 * deg);
    auto* liLogic = new G4LogicalVolume(liSolid, liMaterial, "LiConverter");
    const double liCenterZ = 0.5 * (geom_.liFrontZ + geom_.liRearZ);
    new G4PVPlacement(
        nullptr, G4ThreeVector(0.0, 0.0, liCenterZ), liLogic, "LiConverter",
        worldLogic, false, 0, true);

    return worldPhys;
  }

 private:
  const Config& cfg_;
  GeometryState& geom_;
};

class PrimaryGenerator final : public G4VUserPrimaryGeneratorAction {
 public:
  PrimaryGenerator(const Config& cfg, const GeometryState& geom) : cfg_(cfg), geom_(geom) {
    gun_ = std::make_unique<G4ParticleGun>(1);
    auto* proton = G4ParticleTable::GetParticleTable()->FindParticle("proton");
    gun_->SetParticleDefinition(proton);
    gun_->SetParticleMomentumDirection(G4ThreeVector(0.0, 0.0, 1.0));
    gun_->SetParticleEnergy(cfg_.energyMeV * MeV);
  }

  void GeneratePrimaries(G4Event* event) override {
    gun_->SetParticlePosition(G4ThreeVector(0.0, 0.0, geom_.sourceZ));
    gun_->GeneratePrimaryVertex(event);
  }

 private:
  const Config& cfg_;
  const GeometryState& geom_;
  std::unique_ptr<G4ParticleGun> gun_;
};

class EventAction final : public G4UserEventAction {
 public:
  void BeginOfEventAction(const G4Event*) override {
    exitSeen_.clear();
    detectorSeen_.clear();
  }

  bool MarkExit(int trackId) {
    return exitSeen_.insert(trackId).second;
  }

  bool MarkDetector(int trackId) {
    return detectorSeen_.insert(trackId).second;
  }

 private:
  std::unordered_set<int> exitSeen_;
  std::unordered_set<int> detectorSeen_;
};

class RunAction final : public G4UserRunAction {
 public:
  RunAction(const GeometryState& geom, const Tally& tally) : geom_(geom), tally_(tally) {}

  void EndOfRunAction(const G4Run*) override {
    tally_.Write(geom_);
  }

 private:
  const GeometryState& geom_;
  const Tally& tally_;
};

class SteppingAction final : public G4UserSteppingAction {
 public:
  SteppingAction(const GeometryState& geom, Tally& tally, EventAction& eventAction)
      : geom_(geom), tally_(tally), eventAction_(eventAction) {}

  void UserSteppingAction(const G4Step* step) override {
    const auto* track = step->GetTrack();
    const auto* particle = track->GetParticleDefinition();
    const bool isNeutron = particle && particle->GetParticleName() == "neutron";

    const auto* preVolume = step->GetPreStepPoint()->GetPhysicalVolume();
    const bool inLi = preVolume && preVolume->GetName() == "LiConverter";
    const double preZ = step->GetPreStepPoint()->GetPosition().z();
    const double postZ = step->GetPostStepPoint()->GetPosition().z();

    if (particle && particle->GetParticleName() == "proton" &&
        preZ < geom_.liFrontZ && postZ >= geom_.liFrontZ) {
      tally_.AddPrimaryLiEntry();
    }

    if (inLi) {
      const auto* process = step->GetPostStepPoint()->GetProcessDefinedStep();
      if (process) {
        tally_.AddLiProcess(process->GetProcessName());
      }
      const auto* secondaries = step->GetSecondaryInCurrentStep();
      for (const auto* secondary : *secondaries) {
        const auto particleName = secondary->GetParticleDefinition()->GetParticleName();
        tally_.AddLiSecondary(particleName);
        if (particleName == "neutron") {
          tally_.AddBirth(secondary->GetGlobalTime() / ps, secondary->GetWeight());
        }
      }
    }

    if (!isNeutron) {
      return;
    }

    const double weight = track->GetWeight();
    const double postTimePs = step->GetPostStepPoint()->GetGlobalTime() / ps;

    if (preZ < geom_.liRearZ && postZ >= geom_.liRearZ && eventAction_.MarkExit(track->GetTrackID())) {
      tally_.AddExit(postTimePs, weight);
    }

    if (preZ < geom_.detectorZ && postZ >= geom_.detectorZ &&
        eventAction_.MarkDetector(track->GetTrackID())) {
      tally_.AddDetector(postTimePs, weight);
    }
  }

 private:
  const GeometryState& geom_;
  Tally& tally_;
  EventAction& eventAction_;
};

class ActionInitialization final : public G4VUserActionInitialization {
 public:
  ActionInitialization(const Config& cfg, const GeometryState& geom, Tally& tally)
      : cfg_(cfg), geom_(geom), tally_(tally) {}

  void Build() const override {
    auto* eventAction = new EventAction();
    SetUserAction(new PrimaryGenerator(cfg_, geom_));
    SetUserAction(eventAction);
    SetUserAction(new RunAction(geom_, tally_));
    SetUserAction(new SteppingAction(geom_, tally_, *eventAction));
  }

 private:
  const Config& cfg_;
  const GeometryState& geom_;
  Tally& tally_;
};

double ParseDouble(const std::string& value, const std::string& name) {
  char* end = nullptr;
  const double parsed = std::strtod(value.c_str(), &end);
  if (end == value.c_str() || *end != '\0') {
    throw std::runtime_error("invalid double for " + name + ": " + value);
  }
  return parsed;
}

int ParseInt(const std::string& value, const std::string& name) {
  char* end = nullptr;
  const long parsed = std::strtol(value.c_str(), &end, 10);
  if (end == value.c_str() || *end != '\0' || parsed <= 0) {
    throw std::runtime_error("invalid positive integer for " + name + ": " + value);
  }
  return static_cast<int>(parsed);
}

long ParseLong(const std::string& value, const std::string& name) {
  char* end = nullptr;
  const long parsed = std::strtol(value.c_str(), &end, 10);
  if (end == value.c_str() || *end != '\0') {
    throw std::runtime_error("invalid long for " + name + ": " + value);
  }
  return parsed;
}

void PrintUsage(const char* argv0) {
  std::cout
      << "Usage: " << argv0 << " [options]\n\n"
      << "Options:\n"
      << "  --energy-MeV VALUE          Proton kinetic energy. Default: 5\n"
      << "  --thickness-cm VALUE        Li thickness. Default: 1\n"
      << "  --events VALUE              Primary protons. Default: 10000\n"
      << "  --out-dir PATH              Output directory.\n"
      << "  --physics-list NAME         Reference physics list. Default: QGSP_BIC_HP\n"
      << "  --time-bin-ps VALUE         Time histogram bin width. Default: 1\n"
      << "  --seed VALUE                Random seed. Default: 20260701\n"
      << "  --li-radius-cm VALUE        Li cylinder radius. Default: 2\n"
      << "  --source-gap-cm VALUE       Source to Li front gap. Default: 1\n"
      << "  --detector-gap-cm VALUE     Li rear to detector gap. Default: 10\n"
      << "  --help                      Show this message.\n";
}

Config ParseArgs(int argc, char** argv) {
  Config cfg;
  for (int i = 1; i < argc; ++i) {
    const std::string arg = argv[i];
    auto requireValue = [&](const std::string& name) -> std::string {
      if (i + 1 >= argc) {
        throw std::runtime_error("missing value after " + name);
      }
      return argv[++i];
    };

    if (arg == "--help" || arg == "-h") {
      PrintUsage(argv[0]);
      std::exit(0);
    } else if (arg == "--energy-MeV") {
      cfg.energyMeV = ParseDouble(requireValue(arg), arg);
    } else if (arg == "--thickness-cm") {
      cfg.thicknessCm = ParseDouble(requireValue(arg), arg);
    } else if (arg == "--events") {
      cfg.events = ParseInt(requireValue(arg), arg);
    } else if (arg == "--out-dir") {
      cfg.outDir = requireValue(arg);
    } else if (arg == "--physics-list") {
      cfg.physicsList = requireValue(arg);
    } else if (arg == "--time-bin-ps") {
      cfg.timeBinPs = ParseDouble(requireValue(arg), arg);
    } else if (arg == "--seed") {
      cfg.seed = ParseLong(requireValue(arg), arg);
    } else if (arg == "--li-radius-cm") {
      cfg.liRadiusCm = ParseDouble(requireValue(arg), arg);
    } else if (arg == "--source-gap-cm") {
      cfg.sourceToLiFrontCm = ParseDouble(requireValue(arg), arg);
    } else if (arg == "--detector-gap-cm") {
      cfg.detectorDistanceCm = ParseDouble(requireValue(arg), arg);
    } else {
      throw std::runtime_error("unknown argument: " + arg);
    }
  }

  if (cfg.energyMeV <= 0 || cfg.thicknessCm <= 0 || cfg.liRadiusCm <= 0 ||
      cfg.sourceToLiFrontCm < 0 || cfg.detectorDistanceCm <= 0 || cfg.timeBinPs <= 0) {
    throw std::runtime_error("all geometry, energy and time-bin values must be positive");
  }

  return cfg;
}

int main(int argc, char** argv) {
  try {
    const Config cfg = ParseArgs(argc, argv);
    G4Random::setTheSeed(cfg.seed);

    GeometryState geom;
    Tally tally(cfg);

    auto* runManager = new G4RunManager();
    runManager->SetUserInitialization(new DetectorConstruction(cfg, geom));

    G4PhysListFactory factory;
    auto* physics = factory.GetReferencePhysList(cfg.physicsList);
    if (!physics) {
      throw std::runtime_error("Geant4 could not create physics list: " + cfg.physicsList);
    }
    runManager->SetUserInitialization(physics);
    runManager->SetUserInitialization(new ActionInitialization(cfg, geom, tally));
    runManager->Initialize();
    runManager->BeamOn(cfg.events);

    delete runManager;
  } catch (const std::exception& exc) {
    std::cerr << "li7_benchmark error: " << exc.what() << "\n";
    return 1;
  }

  return 0;
}
