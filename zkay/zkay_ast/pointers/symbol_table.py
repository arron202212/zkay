from typing import Tuple, Dict, Union

from zkay.zkay_ast.ast import AST, SourceUnit, ContractDefinition, VariableDeclaration, \
    SimpleStatement, IdentifierExpr, Block, Mapping, Identifier, Comment, MemberAccessExpr, IndexExpr, LocationExpr, \
    StructDefinition, UserDefinedTypeName, StatementList, Array, ConstructorOrFunctionDefinition, EnumDefinition, \
    EnumValue, NamespaceDefinition, TargetDefinition, VariableDeclarationStatement, ForStatement, IdentifierDeclaration,Parameter
from zkay.zkay_ast.global_defs import GlobalDefs, GlobalVars, array_length_member
from zkay.zkay_ast.pointers.pointer_exceptions import UnknownIdentifierException
from zkay.zkay_ast.visitor.visitor import AstVisitor


def fill_symbol_table(ast):
    v = SymbolTableFiller()
    v.log=True
    v.visit(ast)


def link_symbol_table(ast):
    v = SymbolTableLinker()
    v.is_deepcopy=True
    v.visit(ast)


def link_identifiers(ast):
    # print('====a=====b======')
    fill_symbol_table(ast)
    link_symbol_table(ast)


def merge_dicts(*dict_args):
    """
    Given any number of dicts, shallow copy and merge into a new dict.
    Report error on conflicting keys.
    """
    result = {}
    for dictionary in dict_args:
        for key, value in dictionary.items():
            if key in result and result[key] != value:
                raise ValueError('Conflicting definitions for', key)
            result[key] = value
    return result


def collect_children_names(ast: AST) -> Dict[str, Identifier]:
    children = [c for c in ast.children() if not isinstance(c, (Block, ForStatement))]
    names = [c.names for c in children]
    ret = merge_dicts(*names)
    for c in children: # declared names are not available within the declaration statements
        c.names.clear()
    # print('====collect_children_names==========',ret)
    return ret


def get_builtin_globals():
    sf = SymbolTableFiller()
    return sf.get_builtin_globals()


class SymbolTableFiller(AstVisitor):
    def get_builtin_globals(self):
        global_defs = [d for d in [getattr(GlobalDefs, var) for var in vars(GlobalDefs) if not var.startswith('__')]]
        for d in global_defs:
            self.visit(d)
        global_defs = {d.idf.name: d.idf for d in global_defs}
        global_vars = {d.idf.name: d.idf for d in [getattr(GlobalVars, var) for var in vars(GlobalVars) if not var.startswith('__')]}
        return merge_dicts(global_defs, global_vars)

    def visitSourceUnit(self, ast: SourceUnit):
        ast.names = {c.idf.name: c.idf for c in ast.contracts}
        # print('======ast.names===*****************************=====',ast);
        # print('======get_builtin_globals========',str(self.get_builtin_globals()));
        ast.names.update(self.get_builtin_globals())

    def visitContractDefinition(self, ast: ContractDefinition):
        state_vars = {d.idf.name: d.idf for d in ast.state_variable_declarations if not isinstance(d, Comment)}
        funcs = {}
        for f in ast.function_definitions:
            # print("====f===================",f.idf.name )
            if f.idf.name in funcs:
                raise UnknownIdentifierException(f'Zkay does not currently support method overloading.', f)
            funcs[f.idf.name] = f.idf
        # for s in ast.struct_definitions:
        #     print("=======s================",s.idf.name)
        # for e in ast.enum_definitions:
        #     print("=======e================",e.idf.name)
        structs = {s.idf.name: s.idf for s in ast.struct_definitions}
        enums = {e.idf.name: e.idf for e in ast.enum_definitions}
        ast.names = merge_dicts(state_vars, funcs, structs, enums)

    def visitConstructorOrFunctionDefinition(self, ast: ConstructorOrFunctionDefinition):
        # for e in ast.parameters:
        #     print("=========c==============",e.idf.name)
        ast.names = {p.idf.name: p.idf for p in ast.parameters}

    def visitStructDefinition(self, ast: StructDefinition):
        # for m in ast.members:
        #     print("==sd====name============",m.idf.name)
        ast.names = {m.idf.name: m.idf for m in ast.members}

    def visitEnumDefinition(self, ast: EnumDefinition):
        # for e in ast.values:
            # print("===ed====================",e.idf.name)
        ast.names = {v.idf.name: v.idf for v in ast.values}

    def visitEnumValue(self, ast: EnumValue):
        pass

    def visitVariableDeclaration(self, ast: VariableDeclaration):
        # print("====visitVariableDeclaration===================",ast.idf.name)
        # if ast.idf.name=="votum":
        #             import traceback
        #             for line in traceback.format_stack():
        #                 print(line.strip())
        ast.names = {ast.idf.name: ast.idf}
        # print('====visitVariableDeclaration==========',ast.names)

    def visitStatementList(self, ast: StatementList):
        # print("====visitStatementList===================",type(ast))
        ast.names = collect_children_names(ast)

    def visitSimpleStatement(self, ast: SimpleStatement):
        # print('====visitSimpleStatement==========',type(ast))
        ast.names = collect_children_names(ast)

    def visitForStatement(self, ast: ForStatement):
        ast.names = collect_children_names(ast)

    def visitMapping(self, ast: Mapping):
        ast.names = {}
        if isinstance(ast.key_label, Identifier):
            ast.names = {ast.key_label.name: ast.key_label}


class SymbolTableLinker(AstVisitor):

    @staticmethod
    def _find_next_decl(ast: AST, name: str) -> Tuple[AST, TargetDefinition]:
        # print("======_find_next_decl==============*****************************=====================",name)
        ancestor = ast.parent
        # if name=="secret0_plain_votum":
        #     print(name,'==_find_next_decl=*********************==name anc name=====begin======')
        while ancestor is not None:
            # if name=="secret0_plain_votum":
            #     print(name,'=====names==*******************************==len=======',type(ancestor),len(ancestor.names))
            if name in ancestor.names:
                decl = ancestor.names[name].parent
                # if name=="secret0_plain_votum":
                #     print("========888888========",name,len(ancestor.names),type(ancestor.names[name]),type(decl),"====decl.parent======",type(decl.parent),isinstance(decl.parent, VariableDeclarationStatement), decl.parent.is_parent_of(ast))
                # if decl.parent is None:
                #     print("========decl.parent=====777777777777=========")
                if not isinstance(decl.parent, VariableDeclarationStatement) or not decl.parent.is_parent_of(ast):
                    # if decl.parent is None:
                    #     print("========decl.parent=====9999999=========")
                    # if name=="secret0_plain_votum":
                    #     print(name,'==_find_next_decl===name anc name=====return======',type(ancestor))
                    return ancestor, decl
            ancestor = ancestor.parent
        # if name=="secret0_plain_votum":
        #     print(name,'==_find_next_decl=*****************==name anc name=====fail======')
        raise UnknownIdentifierException(f'Undefined identifier {name}', ast)

    @staticmethod
    def _find_lca(ast1: AST, ast2: AST, root: AST) -> Tuple[StatementList, AST, AST]:
        assert ast1 != ast2

        # Gather ast1's ancestors + immediate child towards ast1 (for each)
        ancs = {}
        while True:
            assert ast1.parent is not None
            ancs[ast1.parent] = ast1
            ast1 = ast1.parent
            if ast1 == root:
                break
        # print(len(ancs))
        # Find least common ancestor with ast2 + immediate child towards ast2
        while True:
            assert ast2.parent is not None
            old_ast = ast2
            ast2 = ast2.parent
            # print(len(ancs),'=======1====',str(ast2))
            if ast2 in ancs:
                assert isinstance(ast2, (ForStatement, StatementList))
                # print("=========",str(ast2))
                return ast2, ancs[ast2], old_ast

    @staticmethod
    def find_type_declaration(t: UserDefinedTypeName) -> NamespaceDefinition:
        # print("====find_type_declaration====name=====", t.names[0].name)
        return SymbolTableLinker._find_next_decl(t, t.names[0].name)[1]

    @staticmethod
    def find_identifier_declaration(ast: IdentifierExpr) -> Union[TargetDefinition, Mapping]:
        name = ast.idf.name
        # print("==========name========",name)
        while True:
            anc, decl = SymbolTableLinker._find_next_decl(ast, name)
            # if ast.code()=="votum":
            #     print("=====================","anc","===========", "decl","===",type(anc),"==========",type(decl))
            if isinstance(anc, (ForStatement, Block)) and isinstance(decl, VariableDeclaration):
                # Check if identifier really references this declaration (does not come before declaration)
                lca, ref_anchor, decl_anchor = SymbolTableLinker._find_lca(ast, decl, anc)
                # print("==len(lca.statements)===",len(lca.statements),lca.statements.index(ref_anchor) , lca.statements.index(decl_anchor))
                if lca.statements.index(ref_anchor) <= lca.statements.index(decl_anchor):
                    ast = anc
                    continue
            # if isinstance(decl,Parameter):
            #     print("=======parameter===************************************=====",ast,"===========",decl)
            return decl

    @staticmethod
    def in_scope_at(target_idf: Identifier, ast: AST) -> bool:
        ancestor = ast.parent
        while ancestor:
            if target_idf.name in ancestor.names and ancestor.names[target_idf.name] == target_idf:
                # found name
                return True
            ancestor = ancestor.parent
        return False

    def visitIdentifierExpr(self, ast: IdentifierExpr):
        # print('===visitIdentifierExpr===***********************======',ast,type(ast))
        decl = self.find_identifier_declaration(ast)
        ast.target = decl
        # print('===visitIdentifierExpr====after=====',type(ast), ast,type(ast.target),"================")
        assert (ast.target is not None)

    def visitUserDefinedTypeName(self, ast: UserDefinedTypeName):
        try:
            type_def = self.find_type_declaration(ast)
            for idf in ast.names[1:]:
                # print("=========name===============",idf.name)
                type_def = type_def.names[idf.name].parent
            ast.target = type_def
            # print("=======visitUserDefinedTypeName====================",ast.code,type_def.code)

        except UnknownIdentifierException:
            pass

    def visitMemberAccessExpr(self, ast: MemberAccessExpr):
        assert isinstance(ast.expr, LocationExpr), "Function call return value member access not yet supported"
        if isinstance(ast.expr.target, NamespaceDefinition):
            ast.target = ast.expr.target.names[ast.member.name].parent
        else:
            t = ast.expr.target.annotated_type.type_name
            if isinstance(t, Array):
                assert ast.member.name == 'length'
                ast.target = array_length_member
            else:
                assert isinstance(t, UserDefinedTypeName)
                if t.target is None:
                    t = t.clone()
                    t.parent = ast
                    self.visit(t)
                if t.target is not None:
                    ast.target = t.target.names[ast.member.name].parent

    def visitIndexExpr(self, ast: IndexExpr):
        assert isinstance(ast.arr, LocationExpr), "Function call return value indexing not yet supported"
        source_t = ast.arr.target.annotated_type.type_name
        # print("===visitIndexExpr===========",ast,"====",ast.arr,"====",type(ast.arr),"====",ast.arr.target,"====",ast.arr.target.annotated_type,type(ast.arr.target),type(ast.arr.target.annotated_type))
        # if isinstance(ast.arr.target,Parameter):
        #     import traceback
        #     for line in traceback.format_stack():
        #         print(line.strip())
        ast.target = VariableDeclaration([], source_t.value_type, Identifier(''))
