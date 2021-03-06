import numpy as np
import mdtraj as md

def superpose(traj_ref):

    """ The function creates a trajectory, superimposed with respect to the frame,
        minimizing sum of Calpha RMSD with respect to all other frames.


       IMPORTANT NOTE: for current version to work, need to use a trajectory, that can be loaded
                       in memory at once, not in chunks 
    """
    

    keep = [a.index for a in traj_ref.topology.atoms if a.name == 'CA']
    traj_alpha = traj_ref.atom_slice(keep)
    
    
    # According to the procedure, described in Olsson2017 papper, need to find a frame, 
    # which minimizes sum of  C_alpha RMSD with respect to all other frames
    # Quadratic algorithm  (O(N2))???
    # Should use C-alpha trajectory!
    #  RMSD matrix is symmetric 
    
    min_idx = 0  
    
    N_frame = traj_ref.n_frames
    RMSD = np.zeros((N_frame,N_frame))
        
    for i in range (0,N_frame):
        for j in range (i,N_frame):
            res = md.rmsd((traj_alpha[i]),(traj_alpha[j]))
            RMSD[i,j] = res
            RMSD[j,i] = res

    sum_RMSD=np.sum(RMSD,axis=0)
    min_idx = np.argmin(sum_RMSD)
    
    traj_ref.superpose(traj_ref, frame=min_idx)
    return(traj_ref)

def superpose2(traj_ref):

    """ The function creates a trajectory, superimposed with respect to the frame,
        minimizing sum of Calpha RMSD with respect to all other frames.


       IMPORTANT NOTE: for current version to work, need to use a trajectory, that can be loaded
                       in memory at once, not in chunks 
    """
    

    keep = [a.index for a in traj_ref.topology.atoms if a.name == 'CA']
    traj_alpha = traj_ref.atom_slice(atoms_to_keep)
    
    
    # According to the procedure, described in Olsson2017 papper, need to find a frame, 
    # which minimizes sum of  C_alpha RMSD with respect to all other frames
    # Quadratic algorithm  (O(N2))???
    # Should use C-alpha trajectory!
    #  RMSD matrix is symmetric 
    
    min_idx = 0  
    
    N_frame = traj_ref.n_frames
    RMSD = np.zeros(N_frame)
        
    for i in range (0,N_frame):
            res = md.rmsd(traj_alpha,traj_alpha[i])
            RMSD[i] = np.sum(res)

    min_idx = np.argmin(RMSD)
    
    traj_ref.superpose(traj_ref, frame=min_idx)
    return(traj_ref)


def superpose3(traj_ref,topology):

    """ The function is based on gromacs procedue. 
        creates a trajectory, superimposed with respect to the frame,
        minimizing sum of Calpha RMSD with respect to all other frames.


       IMPORTANT NOTE:  Code depends on gromacs used 

       Args: traj_ref: path to the trajectory
             topology: GROMACS topology



       
        """
    
    
    
    # According to the procedure, described in Olsson2017 papper, need to find a frame, 
    # which minimizes sum of  C_alpha RMSD with respect to all other frames
    # Quadratic algorithm  (O(N2))???
    # Should use C-alpha trajectory!
    #  RMSD matrix is symmetric 
    
    min_idx = 0  

    min_idx = np.argmin(RMSD)
    
    traj_ref.superpose(traj_ref, frame=min_idx)
    return(traj_ref)



def superpose_large(traj,frames):

    """ The function creates a trajectory, superimposed with respect to the frame,
        minimizing sum of Calpha RMSD with respect to all other frames.


       This virsion streems input trajectory from file.

       traj - name of the input file.
       frames - number of frames to look through for finding    
    """
    

    keep = [a.index for a in traj_ref.topology.atoms if a.name == 'CA']
    # traj_alpha = traj_ref.atom_slice(atoms_to_keep)
    
    
    # According to the procedure, described in Olsson2017 papper, need to find a frame, 
    # which minimizes sum of  C_alpha RMSD with respect to all other frames
    # Quadratic algorithm  (O(N2))???
    # Should use C-alpha trajectory!
    #  RMSD matrix is symmetric 
    
    min_idx = 0  
    
    N_frame = traj_ref.n_frames
    RMSD = np.zeros((N_frame,N_frame))
        
    for i in range(0,N_frame):
        for j in range(i,N_frame):
            res = md.rmsd((traj_ref.atom_slice(keep)[i]),(traj_ref.atom_slice(keep)[j]))
            RMSD[i,j] = res
            RMSD[j,i] = res

    sum_RMSD=np.sum(RMSD,axis=0)
    min_idx = np.argmin(sum_RMSD)
    
    traj_ref.superpose(traj_ref, frame=min_idx)
    return(traj_ref)
