*
* AUTHOR: Sascha Kuhnke
* Created: 20.08.2020
*

SETS

	I				free variables
	
	K				constraints;	

$if not set gdxincname $abort 'No include file name for data file provided'
$gdxin %gdxincname%
$load I K


PARAMETERS

	COEFF(K, I)					coefficients in linear constraint terms
	LOWER(K)					right hand side in constraints
	UPPER(K)					right hand side in constraints
	
	COEFF_OBJ_TIGHTEN_BOUNDS(I)	coefficients in linear objective terms;

$load COEFF LOWER UPPER


SCALARS

	FEAS_TOLERANCE			feasibility tolerance
	
	MODEL_STATUS			model solution status		
	SOLVE_STATUS			solver termination condition
	OBJEST					estimate of the best possible solution
	OBJVAL					objective function value;

$load FEAS_TOLERANCE
$gdxin


FREE VARIABLES

	VAR(I)					free variables;


FREE VARIABLE

	OBJ						objective function;


EQUATIONS

* Constraints
	CONSTR_GE(K)
	CONSTR_LE(K)

* Objective Function
	OBJECTIVE;


* Constraints
	CONSTR_GE(K) ..			SUM(I, COEFF(K, I) * VAR(I))		=G=		LOWER(K);
	CONSTR_LE(K) ..			SUM(I, COEFF(K, I) * VAR(I))		=L=		UPPER(K);
	
* Objective Function
	OBJECTIVE .. 			OBJ 	=E=	 	SUM(I, COEFF_OBJ_TIGHTEN_BOUNDS(I) * VAR(I));


MODEL

	QCP_TIGHTEN_BOUNDS_BOX / ALL /	
	

OPTION

	threads = 1
	sysOut = ON;


QCP_TIGHTEN_BOUNDS_BOX.holdfixed = 1;
QCP_TIGHTEN_BOUNDS_BOX.tolInfeas = FEAS_TOLERANCE;
QCP_TIGHTEN_BOUNDS_BOX.OptFile = 1;
