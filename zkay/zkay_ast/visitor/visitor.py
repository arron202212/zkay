class AstVisitor:

    def __init__(self, traversal='post', log=False,is_deepcopy=False):
        # print("=====AstVisitor======================")
        self.traversal = traversal
        self.log = log
        self.is_deepcopy=is_deepcopy

    def visit(self, ast):
        # if self.is_deepcopy:
        #      print("=====AstVisitor=========visit=============",type(ast))
        return self._visit_internal(ast)

    def _visit_internal(self, ast):
        # if self.log:
        #     print('Visiting', type(ast))
        ret = None
        ret_children = None

        if self.traversal == 'post':
            ret_children = self.visitChildren(ast)
        f = self.get_visit_function(ast.__class__)
        if f is not None:
            ret = f(ast)
        elif self.traversal == 'node-or-children':
            ret_children = self.visitChildren(ast)
        if self.traversal == 'pre':
            ret_children = self.visitChildren(ast)
        if ret is not None:
            # if self.is_deepcopy:
            #     print("=====AstVisitor=========_visit_internal==ret==not=none========",type(ast))
            return ret
        elif ret_children is not None:
            # if self.is_deepcopy:
            #     print("=====AstVisitor=========_visit_internal==ret_children not===none========",type(ast))
            return ret_children
        else:
            # if self.is_deepcopy:
            #     print("=====AstVisitor=========_visit_internal=====none========",type(ast))
            return None

    def get_visit_function(self, c):
        visitor_function = 'visit' + c.__name__
        if hasattr(self, visitor_function):
            return getattr(self, visitor_function)
        else:
            # if self.is_deepcopy:
            #     print("=====AstVisitor=========visit=====base==0======",c)
            for base in c.__bases__:
                # if self.is_deepcopy:
                #     print("=====AstVisitor=========visit=====base========",c,base)
                f = self.get_visit_function(base)
                if f:
                    return f
        # if self.is_deepcopy:
        #     print("=====AstVisitor=========visit=====none========",c)
        return None

    def visitChildren(self, ast):
        # print("=====visitChildren=====begin========",type(ast))
        for c in ast.children():
            # if self.is_deepcopy:
                # print("=====AstVisitor=========visit=====base========",c,base)
                # if type(c)=='zkay.zkay_ast.ast.Parameter' or type(ast)=='zkay.zkay_ast.ast.Parameter':
                # if type(c)=='zkay.zkay_ast.ast.VariableDeclarationStatement':
                # if isinstance(c,IdentifierExpr)
                # try:
                #     # if type(c).__name__=='IdentifierExpr':
                #         print(type(ast),"===visitChildren===^%%%%%%%%%%%%%%%%%%%%=====",type(c))
                # except:
                #     pass
                
            self.visit(c)
        # print("=====visitChildren=====end========",type(ast))
