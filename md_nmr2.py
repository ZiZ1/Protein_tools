import numpy as np
import os
import re
import mdtraj as md

########################################################################################
#
#   The module contains classes and functions needed to calculate NMR data from
#   md traj trajectories.
#   Now implemented calculate_rdc function
#
#
#
############# RDC calculating function and all the dependencies #########################

class Bond:

    def __init__(self, resid_i, resname_i, atomname_i,
                       resid_j, resname_j, atomname_j):
        self.resid_i = resid_i
        self.resname_i = resname_i
        self.atomname_i = atomname_i
        self.resid_j = resid_j
        self.resname_j = resname_j
        self.atomname_j = atomname_j

    def display(self):
        print("resid_i = ", self.resid_i)
        print("resname_i = ", self.resname_i)
        print("atomname_i = ", self.atomname_i)
        print("resid_j = ", self.resid_j)
        print("resname_j = ", self.resname_j)
        print("atomname_i = ", self.atomname_j)





############################################################################################
def normalize(vec):
    """
        Function normalizes a given 3D-vector to 1
    """
    norm_vec = np.divide(vec, np.linalg.norm(vec))
    return(norm_vec)


############################################################################################
def vector(atom_pair, frame):
    """
    Calculate normalized vectors for a specific pair if atoms in a given frame
    """

    vec = frame.xyz[0, atom_pair[1], :]-frame.xyz[0, atom_pair[0], :]
    vec = normalize(vec)
    return vec


##############################################################################################

def bilin(vector):
    """
    Calculate vector of bilinear components based on coordinate vector

    """
    bil = np.empty(5)
    bil[0] =   vector[0]**2-vector[2]**2
    bil[1] =   vector[1]**2-vector[2]**2
    bil[2] = 2*vector[0]*vector[1]
    bil[3] = 2*vector[0]*vector[2]
    bil[4] = 2*vector[1]*vector[2]

    return bil

##################################################################################################

def bilin_matrix(bond_selections, test_frame, noH=False):

    """
    Creates a matrix containing bilinear terms for all bonds,
    listed in bond_selection list"

    Input:   1) bond_selections
                    List, which contain 1 element,
                    for each bond, for which experimental RDC is known.
                    Each element is a list of lenght 2.
                    The first element of a list - integer,
                    corresponding to index of the first atom in the bond.
                    The second element of a list - integer,
                    corresponding to index of the second atom in the bond.
                    Numeration - according to the numeration in MDTraj topology

             2)  test_frame
                    A single MDtraj frame


    Output:   F - numpy array with shape ((len(bond_selections),5))
              Includes bilinear components x^2-z^2, y^2-z^2, 2xy, 2xz, 2yz


    """
    F = np.empty((len(bond_selections), 5))
    i = 0
    if noH == False:
        for (pair) in bond_selections:
            vec = vector(pair, test_frame)
            bil = bilin(vec)
            F[i, :] = bil
            i += 1
    if noH:
        for (pair) in bond_selections:
            vec = get_NH_vector(pair, test_frame)
            bil = bilin(vec)
            F[i, :] = bil
            i += 1
    return F

#####################################################################################################
def get_NH_vector(atoms, frame):
    """ The function extracts CN and C(alpha)N vectors from a given frame and calculates normalized
        NH vector
    """
    CN_vector = vector([atoms[0],atoms[1]], frame)
    CAN_vector = vector([atoms[2],atoms[1]], frame)
    NH_vector = CN_vector + CAN_vector
    NH_vector = normalize(NH_vector)
    return(NH_vector)
#####################################################################################################


def calculate_rdc(traj_ref,RDC_inp_file,minimize_rmsd=True,superimpose=False,mode='average'):

    """
    Calculate residual dipolar couplings for a trajectory, based on experimental values

    Args:

       traj_ref      : MD_traj trajectory

       RDC_inp_file  : file with experimental RDC values.
                      File format is close to NMRPipe, but NOT EXACTLY the same.
                      https://www.ibbr.umd.edu/nmrpipe/install.html

                      Coulumn descriptions:
                      1:  Residue i id
                      2:  Residue i name
                      3:  Atom    i name
                      4:  Residue j id
                      5:  Residue j name
                      6:  Atom    j name
                      7:  RDC for the bond i-j

        minimize_RMSD: Determing, whether superimposion with respect to the frame,
                       minimizing RMSD, will be done.

                       if minimize_RMSD=True (default)  a frame, minimizing
                       sum of  C_alpha RMSD with respect to all other frames is found

                       if minimize_RMSD=False  0-th frame is used to as a reference to super
                       impose all other frames
        superimpose  : Effective only if minimize_RMSD=False. Defaulet - false.
                       If true, all frames are superimposed with respect to 0th frame.


        mode         : Determins the format of the result. If mode="full", the output
                       D_av is an NxM array, where N is a number of frames, M-number of residues.

                       If mode="average" (default), the output is  1d array with lenth M. Each entry -
                       average value over the frame.
    Return: two numpy arrays:
              exp_rdc - experimental values of RDCs
              D_av    -  back-calculated  RDCs


    Dependencies:
                Packages  :   re, np, md
                Classes   :   Bond
                Functions :   bilin_matrix, vector, bilin
    """
    RDC_input = open(RDC_inp_file,'r')

    RDCs=[]
    bonds=[]
    for line in RDC_input.readlines():
        match = re.search(r'^\s*(?P<resid_i>[0-9]+)'
                            '\s*[A-Z]{3}'
                            '\s*(?P<name_i>[A-Z\#]{1,4})'
                            '\s*(?P<resid_j>[0-9]+)'
                            '\s*[A-Z]{3}'
                            '\s*(?P<name_j>[A-Z\#]{1,4})'
                            '\s*(?P<rdc>-?[0-9\.]+)', line)
        if match is None:
            continue
        RDCs.append(float(line.split()[6]))  # Work only when RDC are in the 7 coulumn!
        bonds.append(Bond( int(line.split()[0]),
                              (line.split()[1]),
                              (line.split()[2]),
                           int(line.split()[3]),
                              (line.split()[4]),
                              (line.split()[5]))
                    )

    RDC_input.close()

    atoms_to_keep = [a.index for a in traj_ref.topology.atoms if a.name == 'CA']
    traj_alpha = traj_ref.atom_slice(atoms_to_keep)

    bond_selections=[]
    for bond in bonds:
        # -1 correspond to transition between PDB numeration and MDTRAJ numeration
        # Names of atoms in input files should be the same as one used by mdtraj
        selection_i = traj_ref.top.select('resid %i and name %s' %(bond.resid_i-1, bond.atomname_i))
        assert(selection_i.size != 0)
        selection_j = traj_ref.top.select('resid %i and name %s' %(bond.resid_j-1, bond.atomname_j))
        assert(selection_j.size != 0)
        bond_selections.append([selection_i[0], selection_j[0]])

    # According to the procedure, described in Olsson2017 papper, need to find a frame,
    # which minimizes sum of  C_alpha RMSD with respect to all other frames
    # Quadratic algorithm  (O(N2))???
    # Should use C-alpha trajectory!
    #  RMSD matrix is symmetric

    min_idx = 0

    if minimize_rmsd:
        N_frame = traj_ref.n_frames
        RMSD = np.zeros((N_frame,N_frame))

        for i in range(0,N_frame):
            for j in range(i,N_frame):
                res = md.rmsd(traj_alpha[i],traj_alpha[j])
                RMSD[i,j] = res
                RMSD[j,i] = res

        sum_RMSD=np.sum(RMSD,axis=0)
        min_idx = np.argmin(sum_RMSD)

        traj_ref.superpose(traj_ref, frame=min_idx)

    elif superimpose:
        traj_ref.superpose(traj_ref, frame=min_idx)


    F_av = np.zeros((len(bond_selections),5))
    for i in range (0, traj_ref.n_frames):
        F_av = F_av +  bilin_matrix(bond_selections, traj_ref[i])
    F_av = np.divide(F_av,traj_ref.n_frames)
    A_av, residuals,  rank,s = np.linalg.lstsq(F_av,np.array(RDCs),rcond=-1)

    if mode=='average':
        D_av=np.dot(F_av,A_av)

    if mode=='full':
        D_full=[]
        for i in range(0,traj_ref.n_frames):
            F=bilin_matrix(bond_selections,traj_ref[i])
            D=np.dot(F,A_av)
            D_full.append(D)
        D_av=np.array(D_full)
    exp_rdc=np.array(RDCs)
    return(exp_rdc,D_av)
###########################################################################################################
def calculate_rdc_large(traj,topology,RDC_inp_file, minimize_rmsd=True,mode='average'):

    """
    Calculate residual dipolar couplings based on SVD for a long trajectory,
    when the trajectory cannot be loaded in the memory as a whole.

    Args:

       traj      : trajectory file in any format, supported by md_traj

       topology  : topology file (the same as one for mdtraj)

       RDC_inp_file  : file with experimental RDC values.
                      File format is close to NMRPipe, but NOT EXACTLY the same.
                      https://www.ibbr.umd.edu/nmrpipe/install.html

                      Coulumn descriptions:
                      1:  Residue i id
                      2:  Residue i name
                      3:  Atom    i name
                      4:  Residue j id
                      5:  Residue j name
                      6:  Atom    j name
                      7:  RDC for the bond i-j

        minimize_RMSD: Determing, whether superimposion with respect to the frame,
                       minimizing RMSD, will be done.

                       if minimize_RMSD=True (default)  a frame, minimizing
                       sum of  C_alpha RMSD with respect to all other frames is found

                       if minimize_RMSD=False  0-th frame is used to as a reference to super
                       impose all other frames



    Return: two numpy arrays:
              exp_rdc - experimental values of RDCs
              D_av    -  back-calculated  RDCs


    Dependencies:
                Packages  :   re, np, md
                Classes   :   Bond
                Functions :   bilin_matrix, vector, bilin
    """
    structure=md.load(topology)
    RDC_input = open(RDC_inp_file,'r')

    RDCs=[]
    bonds=[]
    for line in RDC_input.readlines():
        match = re.search(r'^\s*(?P<resid_i>[0-9]+)'
                            '\s*[A-Z]{3}'
                            '\s*(?P<name_i>[A-Z\#]{1,4})'
                            '\s*(?P<resid_j>[0-9]+)'
                            '\s*[A-Z]{3}'
                            '\s*(?P<name_j>[A-Z\#]{1,4})'
                            '\s*(?P<rdc>-?[0-9\.]+)', line)
        if match is None:
            continue
        RDCs.append(float(line.split()[6]))  # Work only when RDC are in the 7 coulumn!
        bonds.append(Bond( int(line.split()[0]),
                              (line.split()[1]),
                              (line.split()[2]),
                           int(line.split()[3]),
                              (line.split()[4]),
                              (line.split()[5]))
                    )

    RDC_input.close()


    bond_selections=[]
    for bond in bonds:
        # -1 correspond to transition between PDB numeration and MDTRAJ numeration
        # Names of atoms in input files should be the same as one used by mdtraj
        selection_i = structure.top.select('resid %i and name %s' %(bond.resid_i-1, bond.atomname_i))
        assert(selection_i.size != 0)
        selection_j = structure.top.select('resid %i and name %s' %(bond.resid_j-1, bond.atomname_j))
        assert(selection_j.size != 0)
        bond_selections.append([selection_i[0], selection_j[0]])

    # According to the procedure, described in Olsson2017 papper, need to find a frame,
    # which minimizes sum of  C_alpha RMSD with respect to all other frames
    # Quadratic algorithm  (O(N2))???
    # Should use C-alpha trajectory!
    #  RMSD matrix is symmetric

    ### From this part, need to use iterator. How can we find superimposed configuration?
    ### Solution: Use a trajectory, that has already been superimposed
    print("NOTE: input trajectory should be superimposed")
    if minimize_rmsd:
        print("WARNING! RMSD minimization is not implemented in current function yet")
        print("Use superimposed trajectory as an input")

    F_av = np.zeros((len(bond_selections),5))
    n_of_frames=0
    print(topology)
    for chunks in md.iterload(traj, chunk=1,top=topology):
        n_of_frames+=1
        F_av = F_av +  bilin_matrix(bond_selections, chunks)
    F_av = np.divide(F_av,n_of_frames)
    A_av, residuals,  rank,s = np.linalg.lstsq(F_av,np.array(RDCs),rcond=-1)


    if mode=='average':
        D_av=np.dot(F_av,A_av)

    if mode=='full':
        D_full=[]
        for chunks in md.iterload(traj, chunk=1,top=topology):
            F=bilin_matrix(bond_selections,chunks)
            D=np.dot(F,A_av)
            D_full.append(D)
        D_av=np.array(D_full)

    exp_rdc=np.array(RDCs)
    return(exp_rdc,D_av)
##############################################################################################################

def calculate_rdc_amide_large(traj, topology, RDC_inp_file, minimize_rmsd=True, mode='average'):
    """
    Calculate residual dipolar couplings for amide NH bond based on SVD for a long trajectory,
    when the trajectory cannot be loaded in the memory as a whole.

    In this case, trajectory can include only backbone reconstruction without any hydrogen atoms.
    The program reads input file and determine corresponding number of residue.

    Args:

       traj      : trajectory file in any format, supported by md_traj

       topology  : topology file (the same as one for mdtraj)

       RDC_inp_file  : file with experimental RDC values.
                      File format is close to NMRPipe, but NOT EXACTLY the same.
                      https://www.ibbr.umd.edu/nmrpipe/install.html

                      Coulumn descriptions:
                      1:  Residue i id
                      2:  Residue i name
                      3:  Atom    i name
                      4:  Residue j id
                      5:  Residue j name
                      6:  Atom    j name
                      7:  RDC for the bond i-j

        minimize_RMSD: Determing, whether superimposion with respect to the frame,
                       minimizing RMSD, will be done.

                       if minimize_RMSD=True (default)  a frame, minimizing
                       sum of  C_alpha RMSD with respect to all other frames is found

                       if minimize_RMSD=False  0-th frame is used to as a reference to super
                       impose all other frames



    Return: two numpy arrays:
              exp_rdc - experimental values of RDCs
              D_av    -  back-calculated  RDCs


    Dependencies:
                Packages  :   re, np, md
                Classes   :   Bond
                Functions :   bilin_matrix, vector, bilin
    """
    structure = md.load(topology)
    RDC_input = open(RDC_inp_file, 'r')

    RDCs = []
    bonds = []
    for line in RDC_input.readlines():
        match = re.search(r'^\s*(?P<resid_i>[0-9]+)'
                          '\s*[A-Z]{3}'
                          '\s*(?P<name_i>[A-Z\#]{1,4})'
                          '\s*(?P<resid_j>[0-9]+)'
                          '\s*[A-Z]{3}'
                          '\s*(?P<name_j>[A-Z\#]{1,4})'
                          '\s*(?P<rdc>-?[0-9\.]+)', line)
        if match is None:
            continue
        RDCs.append(float(line.split()[6]))  # Work only when RDC are in the 7 coulumn!
        assert line.split()[2] == 'N' or line.split()[5] == 'N', "Should have atom N in the bond"
        assert line.split()[2] == 'H' or line.split()[5] == 'H', "Should have atom H  in the bond"
        assert line.split()[0] == line.split()[3], "Atoms in a bond should belong to the same residue"
        assert line.split()[1] == line.split()[4], "Atoms in a bond should belong to the same residue"
        assert line.split()[0] != 1, "RDC calculation for the first residue is not implemented yet. Use trajectory with hydrogens"
        bonds.append(Bond(int(line.split()[0]),
                          (line.split()[1]),
                          (line.split()[2]),
                          int(line.split()[3]),
                          (line.split()[4]),
                          (line.split()[5]))
                     )

    RDC_input.close()

    bond_selections = []
    for bond in bonds:
        # -1 correspond to transition between PDB numeration and MDTRAJ numeration
        # Names of atoms in input files should be the same as one used by mdtraj
        selection_C = structure.top.select('resid %i and name C' % (bond.resid_i-2))
        assert(selection_C.size != 0)
        selection_N = structure.top.select('resid %i and name N' % (bond.resid_j-1))
        assert(selection_N.size != 0)
        selection_CA = structure.top.select('resid %i and name CA' % (bond.resid_j-1))
        assert(selection_CA.size != 0)
        bond_selections.append([selection_C[0], selection_N[0], selection_CA[0]])

    # Use a trajectory, that has already been superimposed
    print("NOTE: input trajectory should be superimposed")
    if minimize_rmsd:
        print("WARNING! RMSD minimization is not implemented in current function yet")
        print("Use superimposed trajectory as an input")
    F_av = np.zeros((len(bond_selections), 5))
    n_of_frames = 0
    print(topology)
    for chunks in md.iterload(traj, chunk=1, top=topology):
        n_of_frames += 1
        F_av = F_av + bilin_matrix(bond_selections, chunks, noH=True)
    F_av = np.divide(F_av, n_of_frames)
    A_av, residuals,  rank, s = np.linalg.lstsq(F_av, np.array(RDCs), rcond=-1)

    if mode == 'average':
        D_av = np.dot(F_av, A_av)

    if mode == 'full':
        D_full = []
        for chunks in md.iterload(traj, chunk=1, top=topology):
            F = bilin_matrix(bond_selections, chunks, noH=True)
            D = np.dot(F, A_av)
            D_full.append(D)
        D_av = np.array(D_full)

    exp_rdc = np.array(RDCs)
    return(exp_rdc, D_av)
####################################################################################################
