import telebot
from telebot import types
from conexao import extrair_cd_localembarque, consulta_clifor, extrai_cidades_rota,extrai_transportadoras
import psycopg2
import fitz

CHAVE_API =  '7888764861:AAHIVmH1WRi2Ps2gDdNR02q4B0O2i43BFhY' # CONSEGUI VIA BOTFATHER
bot = telebot.TeleBot(CHAVE_API) # INSTANCIA O BOT
dados = [] # VARIÁVEL USADA PARA GUARDAR OS DADOS QUE SERÃO ENVIADOS AO BD

@bot.message_handler(commands=['oi', 'faturar'])
def inicio(mensagem):
    global dados 
    dados = []
    texto = """
Bem Vindo ao sistema de faturamento da FV Cereais

Favor informar o seu Login
"""
    bot.send_message(mensagem.chat.id, texto)
    bot.register_next_step_handler(mensagem, login)
def login(mensagem):
    senha_usuario = get_senha(mensagem.text)
    if senha_usuario == 0:
        bot.reply_to(mensagem, "Usuário não existe")
        inicio(mensagem)
    else:
        insere_dados(mensagem.text,consulta_clifor(mensagem.text))
        texto = "Favor informar a sua senha"
        bot.reply_to(mensagem, texto)
        bot.register_next_step_handler(mensagem, senha,senha_usuario) 
def senha(mensagem,senha_usuario): 
    if mensagem.text == senha_usuario:
        insere_dados(mensagem.text,mensagem.from_user.full_name)
        faturar(mensagem)
    else:
        bot.reply_to(mensagem, "Senha incorreta") 
        inicio(mensagem)
def faturar(mensagem): 
    texto = "Informe o número do contrato de venda"
    bot.send_message(mensagem.chat.id, texto) 
    confirma_mensagem(mensagem,1)
def contrato(mensagem,contrato):
    limpa_dados(4)
    try:
        insere_dados(contrato)
        for linhas in extrair_cd_localembarque(int(contrato),dados[1]).values.tolist():
            markup = types.InlineKeyboardMarkup()
            botao_selecionar = types.InlineKeyboardButton("Selecionar", callback_data=str("sel="+str(linhas[2])+"="+str(linhas[0]))) # CRIA O BOTÃO COM O NMR_ORDEM E O CD_ORIGEM
            markup.add(botao_selecionar)
            bot.reply_to(mensagem, str(linhas[1]),reply_markup=markup)
    except:
        bot.send_message(mensagem.chat.id,str("Nenhuma ordem ativa para o contrato "+contrato))
        faturar(mensagem)
def transportadora(mensagem):
    limpa_dados(7)
    bot.send_message(mensagem.chat.id,"Selecione a transportadora")
    try:
        for linhas in extrai_transportadoras(dados[4]):
            print(linhas)
            markup = types.InlineKeyboardMarkup()
            botao_selecionar = types.InlineKeyboardButton("Selecionar", callback_data=str("sel2="+str(linhas))) # CRIA O BOTÃO COM O NMR_ORDEM E O CD_ORIGEM
            markup.add(botao_selecionar)
            bot.reply_to(mensagem, str(linhas),reply_markup=markup)
    except:
        bot.send_message(mensagem.chat.id,str("Nenhuma transportadora ativa para o contrato "+dados[4]))
        faturar(mensagem)
def romaneio(mensagem): 
    limpa_dados(9)
    texto = "Informe o Peso Tara"
    bot.send_message(mensagem.chat.id, texto) # ENVIA A MENSAGEM TEXTO
    bot.register_next_step_handler(mensagem, peso_inicial) # REGISTRA A PROXIMA RESPOSTA
def peso_inicial(mensagem):
    insere_dados(mensagem.text) # INSERE O PESO NA LISTA DADOS
    texto = "Informe o Peso Bruto"
    bot.send_message(mensagem.chat.id, texto) # ENVIA A MENSAGEM TEXTO
    bot.register_next_step_handler(mensagem, confirma_peso) # REGISTRA A PROXIMA RESPOSTA
def confirma_peso(mensagem):
    insere_dados(mensagem.text)
    global dados 
    print(dados)
    markup = botao_confirma(3,"")
    texto = f"""
O pesos informados são:

Peso Tara: {dados[8]}
Peso Bruto: {dados[9]}

Peso líquido: {int(dados[9])-int(dados[8])}

Correto?
"""
    bot.send_message(mensagem.chat.id, texto,reply_markup=markup)
def peso_final(mensagem): 
    bot.reply_to(mensagem, """\
Informe os dados classificados no seguinte formato

UMIDADE
IMPUREZA
AVARIADO
ESVERDEADO
QUEBRADO
""")
    bot.register_next_step_handler(mensagem, categorias) 
def categorias(mensagem): 
    dados = [linha for linha in str(mensagem.text).splitlines() if linha.strip()]
    markup = botao_confirma(4,dados)
    bot.reply_to(mensagem, f"""
Os dados informados foram:
                 
UMIDADE: {dados[0]}
IMPUREZA: {dados[1]}
AVARIADO: {dados[2]}
ESVERDEADO: {dados[3]}
QUEBRADO: {dados[4]}

Correto?
""",reply_markup=markup)

def confirma_mensagem(mensagem,funcao):
    bot.register_next_step_handler(mensagem, confirma_resposta,str(funcao))
def confirma_resposta(mensagem,funcao):
    markup = botao_confirma(funcao,mensagem.text)
    texto = f"""\
O valor informado foi
        
{mensagem.text} 
        
Está correto?              
    """ 
    bot.reply_to(mensagem, str(texto),reply_markup=markup)
def confirma_local(mensagem,nmr_ordem):
    markup = botao_confirma(2,nmr_ordem)
    localembarque = extrair_cd_localembarque(dados[4],dados[1]).values.tolist()
    nm_local = next((item[1] for item in localembarque if item[2] == int(nmr_ordem)), None)
    texto = f"""\
    O valor informado foi
        
    {nm_local} 
        
    Está correto?              
    """ 
    bot.reply_to(mensagem, str(texto),reply_markup=markup)

def botao_confirma(funcao,valor):
    markup = types.InlineKeyboardMarkup()
    botao_sim = types.InlineKeyboardButton("Sim", callback_data=str("botao_sim="+str(funcao)+"="+str(valor)))
    botao_nao = types.InlineKeyboardButton("Não", callback_data=str("botao_nao="+str(funcao)))
    botao_reiniciar = types.InlineKeyboardButton("Reiniciar", callback_data="botao_reiniciar")
    markup.add(botao_nao,botao_sim,botao_reiniciar)
    print(valor," - ",dados)
    return markup
@bot.callback_query_handler()
def resposta_botao(call:types.CallbackQuery):
    global dados
    print(call.data)
    match call.data.split('=')[0]:
        case 'botao_reiniciar':
            inicio(call.message)
        case 'botao_nao':
            match call.data.split('=')[1]:
                case '1' | '2':
                    faturar(call.message)
                case '3':
                    romaneio(call.message)
                case '4':
                    peso_final(call.message)
        case 'botao_sim':
            match call.data.split('=')[1]:
                case '1':
                    contrato(call.message,call.data.split('=')[2])
                case '2':
                    transportadora(call.message)
                case '3':
                    peso_final(call.message)
                case '4':
                    dados.append(call.data.split('=')[2].replace("'",""))
                    dados_bd = {
                        "login":dados[0],
                        "senha":dados[2],
                        "clifor":dados[1],
                        "contato":dados[3],
                        "nr_contrato_venda":dados[4],
                        "rota":dados[5],
                        "ordem":dados[6],
                        "transportadora":dados[7],
                        "peso_inicial":dados[8],
                        "peso_final":dados[9],
                        "classificador":dados[10]
                    }
                    conn = None
                    try:
                        conn = conecta_bd()
                        with conn.cursor() as cursor:
                            inserir = f"INSERT INTO dados_telegram (login, clifor, senha, contato, rota, nr_contrato_venda,ordem,transportadora, peso_inicial, peso_final, classificador, status_ordem) VALUES ('{dados_bd['login']}','{dados_bd['clifor']}', '{dados_bd['senha']}', '{dados_bd['contato']}','{dados_bd['rota']}',{dados_bd['nr_contrato_venda']},{dados_bd['ordem']},'{dados_bd['transportadora']}','{dados_bd['peso_inicial']}','{dados_bd['peso_final']}', ARRAY{dados_bd['classificador']},{False});"
                            cursor.execute(inserir)
                            conn.commit()
                            bot.send_message(call.message.chat.id,"Dados enviados")
                            inicio(call.message)
                    except psycopg2.Error as e:
                        print(f"Erro ao acessar o banco de dados get_senha: {e}")
                        return None
                    finally:
                        if conn:
                            conn.close()
        case 'sel':
            insere_dados(extrai_cidades_rota(call.data.split('=')[2],dados[4]),call.data.split('=')[1])
            print("sel - ",dados)
            confirma_local(call.message,call.data.split('=')[1])
        case 'sel2':
            insere_dados(call.data.split('=')[1])
            print("sel - ",dados)
            romaneio(call.message)

def get_senha(usuario):
    conn = None
    try:
        conn = conecta_bd()
        with conn.cursor() as cursor:
            selecionar = "SELECT senha FROM usuarios WHERE login = %s"
            cursor.execute(selecionar, (usuario,))
            resultado = cursor.fetchone()
            return resultado[0] if resultado else None
    except psycopg2.Error as e:
        print(f"Erro ao acessar o banco de dados get_senha: {e}")
        return None
    finally:
        if conn:
            conn.close()
def insere_dados(*args):
    global dados
    for valor in args:
        dados.append(valor)
def limpa_dados(valor):
    global dados
    try:
        dados = dados[:valor]
    except:
        pass

def conecta_bd():
    host = "localhost" 
    dbname = "automacao_fv"
    user = 'postgres'
    password = 'vjbots'
    port = '5432'
    try:
        conn = psycopg2.connect(
            host=host,
            dbname=dbname,
            user=user,
            password=password,
            port=port
        )
        return conn
    except Exception as e:
        print(f"Erro ao conectar {e}")

bot.remove_webhook()
bot.infinity_polling()
