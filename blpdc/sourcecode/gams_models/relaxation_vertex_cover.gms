*
* AUTHOR: Sascha Kuhnke
* Created: 23.11.2020
*

SETS

	I				variables;	

$if not set gdxincname $abort 'No include file name for data file provided'
$gdxin %gdxincname%
$load I

ALIAS (I, J);


PARAMETERS

	EDGE(I, J)				equals to 1.0 if the edge exisits and 0.0 otherwise;	

$load EDGE


SCALARS

	FEAS_TOLERANCE			feasibility tolerance
	
	MODEL_STATUS			model solution status		
	SOLVE_STATUS			solver termination condition
	OBJEST					estimate of the best possible solution
	OBJVAL					objective function value;

$load FEAS_TOLERANCE
$gdxin


POSITIVE VARIABLES

	VAR(I)					continuous variables;


FREE VARIABLE

	OBJ						objective function;


* Bounds
	VAR.Lo(I) = 0.0;
	VAR.Up(I) = 1.0;


EQUATIONS

* Constraints
	CONSTR(I, J)

* Objective Function
	OBJECTIVE;


* Constraints
	CONSTR(I, J) $ EDGE(I, J) ..			VAR(I) + VAR(J)			=G=		1.0;
	
* Objective Function
	OBJECTIVE .. 								OBJ 	=E=	 	SUM(I, VAR(I));


MODEL

	RELAXATION_VERTEX_COVER / ALL /	
	

OPTION

	threads = 1
	sysOut = ON;	


RELAXATION_VERTEX_COVER.holdfixed = 1;
RELAXATION_VERTEX_COVER.tolInfeas = FEAS_TOLERANCE;
RELAXATION_VERTEX_COVER.OptFile = 1;

