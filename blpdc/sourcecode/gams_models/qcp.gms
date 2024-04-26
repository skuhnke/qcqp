*
* AUTHOR: Sascha Kuhnke
* Created: 09.06.2020
*

SETS

	I				free variables
	
	K				constraints
	K_EQ(K)			equality constraints
	K_GE(K)			greater or equal constraints
	K_LE(K)			less or equal constraints;	

$if not set gdxincname $abort 'No include file name for data file provided'
$gdxin %gdxincname%
$load I K K_EQ K_GE K_LE


ALIAS (I, J);


PARAMETERS

	COEFF_QUAD(K, I, J)		coefficients in quadratic constraint terms
	COEFF(K, I)				coefficients in linear constraint terms
	RHS(K)					right hand side in constraints
	
 	COEFF_QUAD_OBJ(I, J)	coefficients in quadratic objective terms
	COEFF_OBJ(I)			coefficients in linear objective terms

	BOUND_LO(I)				lower bounds of variables
	BOUND_UP(I)				upper bounds of variables;	

$load COEFF_QUAD COEFF RHS COEFF_QUAD_OBJ COEFF_OBJ BOUND_LO BOUND_UP


SCALARS

	FEAS_TOLERANCE			feasibility tolerance
	FEAS_TOLERANCE_CHECKER	feasibility tolerance for solution checker
	
	MODEL_STATUS			model solution status		
	SOLVE_STATUS			solver termination condition
	OBJEST					estimate of the best possible solution
	OBJVAL					objective function value;

$load FEAS_TOLERANCE FEAS_TOLERANCE_CHECKER
$gdxin


FREE VARIABLES

	VAR(I)					free variables;


FREE VARIABLE

	OBJ						objective function;


* Bounds
	VAR.Lo(I) = BOUND_LO(I);
	VAR.Up(I) = BOUND_UP(I);


EQUATIONS

* Constraints
	CONSTR_EQ(K_EQ)
	CONSTR_GE(K_GE)
	CONSTR_LE(K_LE)

* Objective Function
	OBJECTIVE;


* Constraints
	CONSTR_EQ(K_EQ) ..	SUM((I, J), COEFF_QUAD(K_EQ, I, J) * VAR(I) * VAR(J)) + SUM(I, COEFF(K_EQ, I) * VAR(I))		=E=		RHS(K_EQ);
	CONSTR_GE(K_GE) ..	SUM((I, J), COEFF_QUAD(K_GE, I, J) * VAR(I) * VAR(J)) + SUM(I, COEFF(K_GE, I) * VAR(I))		=G=		RHS(K_GE);
	CONSTR_LE(K_LE) ..	SUM((I, J), COEFF_QUAD(K_LE, I, J) * VAR(I) * VAR(J)) + SUM(I, COEFF(K_LE, I) * VAR(I))		=L=		RHS(K_LE);
	
* Objective Function
	OBJECTIVE .. 			OBJ 	=E=	 	SUM((I, J), COEFF_QUAD_OBJ(I, J) * VAR(I) * VAR(J)) + SUM(I, COEFF_OBJ(I) * VAR(I));


MODEL

	QCP / ALL /	
	QCP_CHECKER / ALL /;
	

OPTION

	threads = 1
	sysOut = ON;


QCP.holdfixed = 1;
QCP.tolInfeas = FEAS_TOLERANCE;
QCP.OptFile = 1;

QCP_CHECKER.holdfixed = 1;
QCP_CHECKER.tolInfeas = FEAS_TOLERANCE_CHECKER;
QCP_CHECKER.OptFile = 1;

