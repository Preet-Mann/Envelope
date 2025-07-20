import math
import random
import ROOT


# --- Generation and Assignment ---
class EventSimulator:

    # Variable Dictionary
    # Additional particles can be added here, changing the vertex and momentum constraints can be done here
    def __init__(self, output_file, n_events=10000):
        self.output_file = output_file
        self.n_events = n_events
        self.min_mom = 3.0 # Lower limit of momentum - 3 G/eV
        self.max_mom = 10.0 # Upper limit of momentum - 10 G/eV
        self.square_side = 300.0 # Limits vertex region
        self.rng = ROOT.TRandom3(0)
        self.PARTICLE_DATA = {
            "1": {"name": "pion", "pdg_id": 211, "mass": 0.13957039},
            "2": {"name": "kaon", "pdg_id": 321, "mass": 0.493677},
            "3": {"name": "proton", "pdg_id": 2212, "mass": 0.93827208816},
        }

    # Prompt User for Particle Species
    # Additional particle prompts can be added here
    def get_particle_choice(self):
        while True:
            print("\nOptions:")
            print("1. Pion")
            print("2. Kaon")
            print("3. Proton")
            choice = input("Enter your choice: ")
            if choice in self.PARTICLE_DATA:
                return self.PARTICLE_DATA[choice]
            print("Invalid input. Please enter 1, 2, or 3.")

    # Randomly Generates x,y,z momentum in a given range
    def generate_momentum(self):
        while True:
            p = self.rng.Gaus(6.5, 1.0)
            if self.min_mom <= p <= self.max_mom:
                break
        theta = random.uniform(0, math.pi)
        phi = random.uniform(0, 2 * math.pi)
        px = p * math.sin(theta) * math.cos(phi)
        py = p * math.sin(theta) * math.sin(phi)
        pz = p * math.cos(theta)
        return px, py, pz, p

    # Randomly Generates x,y vertex coordinates in a given range, this range can be editted via self.square_side =... in the variable dictionary
    def generate_vertex(self):
        while True:
            vx = self.rng.Gaus(0, 50)
            if -self.square_side / 2 <= vx <= self.square_side / 2:
                break
        while True:
            vy = self.rng.Gaus(0, 50)
            if -self.square_side / 2 <= vy <= self.square_side / 2:
                break
        vz = 0.0
        return vx, vy, vz

    # Event details for hepmc output file
    def write_event(self, f, event_id, px, py, pz, E, vx, vy, vz, pdg_id):
        f.write(f"E {event_id} 0 0 0 0 0\n")
        f.write("F GenEvent 3 0\n")
        f.write("F Units 0 0\n")
        f.write("F MomentumUnit GEV\n")
        f.write("F LengthUnit MM\n")
        f.write(f"F GenParticle 1 1 {pdg_id} 1 0 0 0 0 {px:.6f} {py:.6f} {pz:.6f} {E:.6f}\n")
        f.write(f"F GenVertex 1 -1 -1 -1 {vx:.3f} {vy:.3f} {vz:.3f} 0.0\n")
        f.write("F GenParticle 1\n")
        f.write("F GenVertex 1\n")

    # Writes out events to HepMc file
    def generate_events(self):
        particle = self.get_particle_choice()
        mass = particle["mass"]
        pdg_id = particle["pdg_id"]

        with open(self.output_file, "w") as f:
            f.write("HepMC::Version 3.0.0\n")
            f.write("HepMC::IO_GenEvent-START_EVENT_LISTING\n")
            for event_id in range(self.n_events):
                px, py, pz, p_mag = self.generate_momentum()
                vx, vy, vz = self.generate_vertex()
                E = math.sqrt(p_mag**2 + mass**2)
                self.write_event(f, event_id, px, py, pz, E, vx, vy, vz, pdg_id)
            f.write("HepMC::IO_GenEvent-END_EVENT_LISTING\n")
        print(f"Wrote {self.n_events} events to {self.output_file}")



# Plotting and Fitting
class PlotManager:
    def __init__(self, input_file):
        self.input_file = input_file
        self.hist_vertex_raw = ROOT.TH2F("vertex", "Vertex Distribution;X (mm);Y (mm)", 100, -200, 200, 100, -200, 200)
        self.hist_momentum_raw = ROOT.TH1F("momentum", "Momentum Magnitude;|p| (GeV);Events", 100, 0, 12)
        self.c_vertex = None
        self.c_momentum = None
        self.plotted_hist_vertex = None
        self.plotted_hist_momentum = None
        self.fit_vertex = None
        self.fit_momentum = None
        self.load_data()

    # Loads vertex and momentum data by parsing hepmc file
    def load_data(self):
        with open(self.input_file, "r") as f:
            for line in f:
                if line.startswith("F GenVertex"): #reads x/y vertex info from hepmc file, fills vertex graph
                    parts = line.strip().split()
                    if len(parts) >= 8:
                        try:
                            vx = float(parts[6])
                            vy = float(parts[7])
                            self.hist_vertex_raw.Fill(vx, vy)
                        except ValueError:
                            pass
                elif line.startswith("F GenParticle"): #reads particle momentum from hepmc file and calculates the magnitude of the momentum, fills momentum histogram
                    parts = line.strip().split()
                    if len(parts) >= 13:
                        try:
                            px = float(parts[10])
                            py = float(parts[11])
                            pz = float(parts[12])
                            p_mag = math.sqrt(px**2 + py**2 + pz**2)
                            self.hist_momentum_raw.Fill(p_mag)
                        except ValueError:
                            pass

    # Create canvases for vertex and momentum plots
    def create_canvases(self):
        if not self.c_vertex:
            self.c_vertex = ROOT.TCanvas("c_vertex", "Vertex Plot", 800, 600)
        if not self.c_momentum:
            self.c_momentum = ROOT.TCanvas("c_momentum", "Momentum Plot", 800, 600)


    # Plots vertex and momentum histograms
    def plot_histograms(self, fit=False):
            self.create_canvases()
            v_hist_name = f"hist_vertex_{ROOT.gRandom.Integer(100000)}"
            self.plotted_hist_vertex = self.hist_vertex_raw.Clone(v_hist_name)

            m_hist_name = f"hist_momentum_{ROOT.gRandom.Integer(100000)}"
            self.plotted_hist_momentum = self.hist_momentum_raw.Clone(m_hist_name)
            #plot styling
            from ROOT import gStyle
            gStyle.SetOptFit(4)
            gStyle.SetOptStat(0)
            self.plotted_hist_momentum.GetXaxis().CenterTitle()
            self.plotted_hist_momentum.GetYaxis().CenterTitle()
            self.plotted_hist_vertex.GetXaxis().CenterTitle()
            self.plotted_hist_vertex.GetYaxis().CenterTitle()
            self.plotted_hist_vertex.GetYaxis().SetTitleOffset(0.9)


       # Vertex canvas
            self.c_vertex.cd()
            self.c_vertex.Clear()
            self.plotted_hist_vertex.Draw("COLZ")
            if fit:
                v_fit_name = f"fit2d_{ROOT.gRandom.Integer(100000)}" # This is for debugging purposes, without it the histogram loses its data when clicked on, attempts to call a plot that is no longer stored
                self.fit_vertex = ROOT.TF2(v_fit_name, "[0]*exp(-0.5*((x/[1])**2 + (y/[2])**2))", -150, 150, -150, 150)
                self.fit_vertex.SetParameters(1, 50, 50)
                self.plotted_hist_vertex.Fit(self.fit_vertex, "RS")
            self.c_vertex.Update()

        # Momentum canvas
            self.c_momentum.cd()
            self.c_momentum.Clear()
            self.plotted_hist_momentum.Draw()
            if fit:
                m_fit_name = f"fit1d_{ROOT.gRandom.Integer(100000)}" # Same debugging line
                self.fit_momentum = ROOT.TF1(m_fit_name, "gaus", 0, 12)
                self.plotted_hist_momentum.Fit(self.fit_momentum, "RS")
            self.c_momentum.Update()

    # Allows user to view unfitted or fitted plots continuously
    def interactive_plot(self):
        while True:
            print("\nPlot Options:")
            print("1. Unfitted Distributions")
            print("2. Fitted Distributions")
            print("0. Exit")
            choice = input("Enter your choice: ")

            if choice == "1":
                self.plot_histograms(fit=False)
            elif choice == "2":
                self.plot_histograms(fit=True)
            elif choice == "0":
                print("Exit...")
                if self.c_vertex:
                    self.c_vertex.Close()
                if self.c_momentum:
                    self.c_momentum.Close()
                break
            else:
                print("Invalid...")



def main():
    output_file = "flat_particle_ascii.hepmc" # Edit name of output file here
    n_events = 10000 # Edit the number of events here

    simulator = EventSimulator(output_file, n_events)
    simulator.generate_events()

    plotter = PlotManager(output_file)
    plotter.interactive_plot()

if __name__ == "__main__":
    main()
