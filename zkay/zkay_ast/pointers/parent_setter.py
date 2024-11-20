from zkay.zkay_ast.ast import AST, IdentifierExpr,Expression, Statement, ConstructorOrFunctionDefinition,FunctionCallExpr,RequireStatement, VariableDeclarationStatement,SourceUnit, NamespaceDefinition, VariableDeclaration,Identifier,Mapping,AddressTypeName
from zkay.zkay_ast.visitor.visitor import AstVisitor


class ParentSetterVisitor(AstVisitor):
    """
    Links parents
    """

    def __init__(self):
        # print("====ParentSetterVisitor=========================================================")
        super().__init__(traversal='pre')

    def visitSourceUnit(self, ast: SourceUnit):
        ast.namespace = []

    def visitNamespaceDefinition(self, ast: NamespaceDefinition):
        ast.namespace = ([] if ast.parent is None else ast.parent.namespace) + [ast.idf]

    def visitConstructorOrFunctionDefinition(self, ast: ConstructorOrFunctionDefinition):
        ast.namespace = ([] if ast.parent is None else ast.parent.namespace) + [ast.idf]

    def visitChildren(self, ast: AST):
        
        for c in ast.children():
            if c is None:
                print(c, ast, ast.children())
            # if  getattr(c,"code") and c.code()=="votum":
            # if isinstance(c, IdentifierExpr):
            # try:
            #     if c.code()=="votum" or isinstance(c,VariableDeclaration,VariableDeclarationStatement,FunctionCallExpr,RequireStatement) :
            #         print("===parent=======visitChildren=======",type(ast),type(c))
            # except Exception as e:
            #     # print(e)
            #     pass
            c.parent = ast
            c.namespace = ast.namespace
            # print(type(ast),type(c))
            self.visit(c)


class ExpressionToStatementVisitor(AstVisitor):

    def visitExpression(self, ast: Expression):
        parent = ast
        while parent and not isinstance(parent, Statement):
            parent = parent.parent
        if parent:
            # print("==ExpressionToStatementVisitor=======",type(ast),parent,type(parent))
            ast.statement = parent

    def visitStatement(self, ast: Statement):
        parent = ast
        while parent and not isinstance(parent, ConstructorOrFunctionDefinition):
            parent = parent.parent
        if parent:
            ast.function = parent


def set_parents(ast):
    v = ParentSetterVisitor()
    v.visit(ast)
    v = ExpressionToStatementVisitor()
    v.visit(ast)
