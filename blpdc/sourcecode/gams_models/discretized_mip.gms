*
* AUTHOR: Sascha Kuhnke
* Created: 06.08.2020
*

SETS

	I				free variables
	I_DISC(I)		discretized variables
	
	K				constraints
	K_EQ(K)			equality constraints
	K_GE(K)			greater or equal constraints
	K_LE(K)			less or equal constraints
	N				indices for discretization;	

$if not set gdxincname $abort 'No include file name for data file provided'
$gdxin %gdxincname%
$load I I_DISC K K_EQ K_GE K_LE N


ALIAS (I, J);


PARAMETERS

	COEFF_QUAD(K, I_DISC, J)	coefficients in quadratic constraint terms
	COEFF(K, I)					coefficients in linear constraint terms
	RHS(K)						right hand side in constraints
	
 	COEFF_QUAD_OBJ(I_DISC, J)	coefficients in quadratic objective terms
	COEFF_OBJ(I)				coefficients in linear objective terms

	BOUND_LO(I)					lower bounds of variables
	BOUND_UP(I)					upper bounds of variables
	
	IS_BILINEAR(I, J)			equals 1.0 if the corresponding bilinear term is present 
	IS_SQUARED(I)				equals 1.0 if the corresponding variable is squared
	VALUE_DISC(I_DISC, N)		discretized values;	

$load COEFF_QUAD COEFF RHS COEFF_QUAD_OBJ COEFF_OBJ BOUND_LO BOUND_UP IS_BILINEAR IS_SQUARED


SCALARS
	
	ONE						equals one								/ 1 /
	FEAS_TOLERANCE			feasibility tolerance
	
	MODEL_STATUS			model solution status		
	SOLVE_STATUS			solver termination condition
	OBJEST					estimate of the best possible solution
	OBJVAL					objective function value;

$load FEAS_TOLERANCE
$gdxin


FREE VARIABLES

	VAR(I)					free variables
	VAR_DISC(I_DISC, J, N)	auxiliary variables for discretization;
	

BINARY VARIABLES

	CHI(I_DISC, N)			selection of discretized values;	


FREE VARIABLE

	OBJ						objective function;


* Bounds
	VAR.Lo(I) = BOUND_LO(I);
	VAR.Up(I) = BOUND_UP(I);


EQUATIONS

* Constraints
	DISC_CONSTR_EQ(K_EQ)
	DISC_CONSTR_GE(K_GE)
	DISC_CONSTR_LE(K_LE)
	
* Discretization
	DISC_VAR(I_DISC)
	DISC_SOS(I_DISC)	
	DISC_SUM(I_DISC, J)
	DISC_LO(I_DISC, J, N)
	DISC_UP(I_DISC, J, N)

* Objective Function
	OBJECTIVE;


* Constraints
	DISC_CONSTR_EQ(K_EQ) ..	SUM((I_DISC, J) $ IS_BILINEAR(I_DISC, J), COEFF_QUAD(K_EQ, I_DISC, J) * SUM(N, VALUE_DISC(I_DISC, N) * VAR_DISC(I_DISC, J, N))) + 
							SUM(I_DISC $ IS_SQUARED(I_DISC), COEFF_QUAD(K_EQ, I_DISC, I_DISC) * SUM(N, POWER(VALUE_DISC(I_DISC, N), 2) * CHI(I_DISC, N))) + 
							SUM(I, COEFF(K_EQ, I) * VAR(I))		=E=		RHS(K_EQ);
	DISC_CONSTR_GE(K_GE) ..	SUM((I_DISC, J) $ IS_BILINEAR(I_DISC, J), COEFF_QUAD(K_GE, I_DISC, J) * SUM(N, VALUE_DISC(I_DISC, N) * VAR_DISC(I_DISC, J, N))) + 
							SUM(I_DISC $ IS_SQUARED(I_DISC), COEFF_QUAD(K_GE, I_DISC, I_DISC) * SUM(N, POWER(VALUE_DISC(I_DISC, N), 2) * CHI(I_DISC, N))) +	
														SUM(I, COEFF(K_GE, I) * VAR(I))		=G=		RHS(K_GE);
	DISC_CONSTR_LE(K_LE) ..	SUM((I_DISC, J) $ IS_BILINEAR(I_DISC, J), COEFF_QUAD(K_LE, I_DISC, J) * SUM(N, VALUE_DISC(I_DISC, N) * VAR_DISC(I_DISC, J, N))) + 
							SUM(I_DISC $ IS_SQUARED(I_DISC), COEFF_QUAD(K_LE, I_DISC, I_DISC) * SUM(N, POWER(VALUE_DISC(I_DISC, N), 2) * CHI(I_DISC, N))) +	
							SUM(I, COEFF(K_LE, I) * VAR(I))		=L=		RHS(K_LE);
	
* Discretization
	DISC_VAR(I_DISC) ..									VAR(I_DISC)					=E=		SUM(N, VALUE_DISC(I_DISC, N) * CHI(I_DISC, N));
	DISC_SOS(I_DISC) ..									SUM(N, CHI(I_DISC, N)) 		=E=		ONE;	
	DISC_SUM(I_DISC, J) $ IS_BILINEAR(I_DISC, J) ..		VAR(J)						=E=		SUM(N, VAR_DISC(I_DISC, J, N));
	DISC_LO(I_DISC, J, N) $ IS_BILINEAR(I_DISC, J) ..	VAR_DISC(I_DISC, J, N)		=G= 	BOUND_LO(J) * CHI(I_DISC, N);
	DISC_UP(I_DISC, J, N) $ IS_BILINEAR(I_DISC, J) ..	VAR_DISC(I_DISC, J, N)		=L= 	BOUND_UP(J) * CHI(I_DISC, N);
	
* Objective Function
	OBJECTIVE .. 			OBJ 	=E=	 	SUM((I_DISC, J) $ IS_BILINEAR(I_DISC, J), COEFF_QUAD_OBJ(I_DISC, J) * SUM(N, VALUE_DISC(I_DISC, N) * VAR_DISC(I_DISC, J, N))) + 
											SUM(I_DISC $ IS_SQUARED(I_DISC), COEFF_QUAD_OBJ(I_DISC, I_DISC) * SUM(N, POWER(VALUE_DISC(I_DISC, N), 2) * CHI(I_DISC, N))) + 	
											SUM(I, COEFF_OBJ(I) * VAR(I));


MODEL

	DISCRETIZED_MIP / ALL /	
	

OPTION

	threads = 1
	sysOut = ON;


DISCRETIZED_MIP.holdfixed = 1;
DISCRETIZED_MIP.tolInfeas = FEAS_TOLERANCE;
DISCRETIZED_MIP.OptFile = 1;

