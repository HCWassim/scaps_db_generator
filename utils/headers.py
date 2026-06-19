def iv_header(iv_points=85):
    txt1, txt2 = "", ""
    for i in range(iv_points):
        txt1 += f"V{i+1},"
        txt2 += f"I{i+1},"

    return f"{txt1}{txt2}Voc,Jsc,FF,eta,V_MPP,J_MPP,T,N_A,N_t,mu_h,intensity,ID_def\n"


def qe_header(qe_points=61):
    txt1, txt2 = "", ""
    for i in range(qe_points):
        txt1 += f"lambda{i+1},"
        txt2 += f"QE{i+1},"

    return f"{txt1}{txt2}T,N_A,N_t,mu_h,intensity,ID_def\n"

print(qe_header())