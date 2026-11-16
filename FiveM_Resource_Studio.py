import os, re, zipfile, shutil, threading, csv, tkinter as tk, json, hashlib, fnmatch
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

APP = "FiveM Resource Studio"
TEXT_EXT = {".lua", ".cfg", ".json", ".xml", ".meta", ".txt", ".md", ".sql", ".html", ".css", ".js", ".yml", ".yaml"}
MAP_EXT = {".ymap", ".ytyp", ".ymf", ".ybn", ".ydr", ".ydd", ".ytd", ".yft"}

class Studio(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP + " V0.2.0 Beta")
        self.geometry("1120x720")
        self.minsize(900, 600)
        self.configure(bg="#101522")
        self.zip_path = None
        self.workdir = None
        self.current_file = None
        self.coords_data = []
        self.entities_data = []
        self.xml_trees = {}
        self.selected_entity = None
        self._style()
        self._ui()

    def _style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("Treeview", background="#151e2e", foreground="#e8edf7",
                    fieldbackground="#151e2e", rowheight=27, borderwidth=0)
        s.map("Treeview", background=[("selected", "#284d78")])
        s.configure("TButton", background="#263b58", foreground="white",
                    padding=8, borderwidth=0)
        s.map("TButton", background=[("active", "#34577f")])
        s.configure("TLabel", background="#101522", foreground="#dce5f2")
        s.configure("Header.TLabel", font=("Segoe UI", 18, "bold"), foreground="#ffffff")
        s.configure("Sub.TLabel", font=("Segoe UI", 9), foreground="#91a5bf")
        s.configure("TNotebook", background="#101522", borderwidth=0)
        s.configure("TNotebook.Tab", background="#1a2638", foreground="#dce5f2", padding=(14, 8))
        s.map("TNotebook.Tab", background=[("selected", "#284d78")])

    def _ui(self):
        header = tk.Frame(self, bg="#111b2b", height=76)
        header.pack(fill="x")
        tk.Label(header, text="FIVEM RESOURCE STUDIO · BETA", bg="#111b2b", fg="white",
                 font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=22, pady=(13,0))
        tk.Label(header, text="V0.2.0 Beta · Análisis inteligente de archivos · Diagnóstico Lua · Permisos ACE opcionales · Editor", bg="#111b2b",
                 fg="#91a5bf", font=("Segoe UI", 9)).pack(anchor="w", padx=23)
        actions = tk.Frame(self, bg="#101522")
        actions.pack(fill="x", padx=18, pady=12)
        ttk.Button(actions, text="＋ Cargar ZIP", command=self.load_zip).pack(side="left", padx=(0,8))
        ttk.Button(actions, text="Abrir carpeta", command=self.open_folder).pack(side="left", padx=4)
        ttk.Button(actions, text="Extraer archivos accesibles", command=self.extract).pack(side="left", padx=4)
        ttk.Button(actions, text="Guardar archivo editado", command=self.save_file).pack(side="left", padx=4)
        ttk.Button(actions, text="Crear ZIP final", command=self.pack_zip).pack(side="left", padx=4)
        ttk.Button(actions, text="Buscar archivo/texto", command=self.search_content).pack(side="left", padx=4)
        ttk.Button(actions, text="Exportar coordenadas CSV", command=self.export_coords).pack(side="left", padx=4)
        ttk.Button(actions, text="Auditar recurso", command=self.audit_resource).pack(side="left", padx=4)
        ttk.Button(actions, text="Exportar entidades CSV", command=self.export_entities).pack(side="left", padx=4)
        self.status = tk.StringVar(value="Carga un recurso ZIP o abre una carpeta.")
        tk.Label(actions, textvariable=self.status, bg="#101522", fg="#91a5bf").pack(side="right")

        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, padx=18, pady=(0,14))
        self.tab_files = tk.Frame(self.tabs, bg="#101522")
        self.tab_report = tk.Frame(self.tabs, bg="#101522")
        self.tab_editor = tk.Frame(self.tabs, bg="#101522")
        self.tab_maps = tk.Frame(self.tabs, bg="#101522")
        self.tab_entity = tk.Frame(self.tabs, bg="#101522")
        self.tab_recovery = tk.Frame(self.tabs, bg="#101522")
        self.tab_permissions = tk.Frame(self.tabs, bg="#101522")
        self.tabs.add(self.tab_files, text="  Archivos  ")
        self.tabs.add(self.tab_report, text="  Análisis  ")
        self.tabs.add(self.tab_editor, text="  Editor Lua / texto  ")
        self.tabs.add(self.tab_maps, text="  Mapas y coordenadas  ")
        self.tabs.add(self.tab_entity, text="  Editor de entidades  ")
        self.tabs.add(self.tab_recovery, text="  Recuperación de recursos  ")
        self.tabs.add(self.tab_permissions, text="  Permisos ACE opcionales  ")

        left = tk.Frame(self.tab_files, bg="#101522")
        left.pack(fill="both", expand=True, padx=12, pady=12)
        tk.Label(left, text="Contenido del recurso", bg="#101522", fg="white",
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0,8))
        self.tree = ttk.Treeview(left, columns=("size","type"), show="tree headings")
        self.tree.heading("#0", text="Ruta")
        self.tree.heading("size", text="Tamaño")
        self.tree.heading("type", text="Tipo")
        self.tree.column("#0", width=650)
        self.tree.column("size", width=110, anchor="e")
        self.tree.column("type", width=120)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", self.open_selected)

        self.report = tk.Text(self.tab_report, bg="#151e2e", fg="#e8edf7",
                              insertbackground="white", wrap="word", font=("Consolas", 10),
                              relief="flat", padx=12, pady=12)
        self.report.pack(fill="both", expand=True, padx=12, pady=12)

        self.editor = tk.Text(self.tab_editor, bg="#151e2e", fg="#e8edf7",
                              insertbackground="white", wrap="none", font=("Consolas", 10),
                              undo=True, relief="flat", padx=12, pady=12)
        self.editor.pack(fill="both", expand=True, padx=12, pady=12)

        self.maps = tk.Text(self.tab_maps, bg="#151e2e", fg="#e8edf7",
                            insertbackground="white", wrap="word", font=("Consolas", 10),
                            relief="flat", padx=12, pady=12)
        self.maps.pack(fill="both", expand=True, padx=12, pady=12)

        ent_top=tk.Frame(self.tab_entity,bg="#101522")
        ent_top.pack(fill="both",expand=True,padx=12,pady=12)
        tk.Label(ent_top,text="Entidades leídas desde XML",bg="#101522",fg="white",
                 font=("Segoe UI",11,"bold")).pack(anchor="w",pady=(0,8))
        self.entity_tree=ttk.Treeview(ent_top,columns=("x","y","z","file"),show="tree headings",height=12)
        self.entity_tree.heading("#0",text="Entidad / archetype")
        for col in ("x","y","z","file"): self.entity_tree.heading(col,text=col.upper() if col!="file" else "Archivo")
        self.entity_tree.column("#0",width=250)
        self.entity_tree.column("x",width=105); self.entity_tree.column("y",width=105)
        self.entity_tree.column("z",width=105); self.entity_tree.column("file",width=360)
        self.entity_tree.pack(fill="both",expand=True)
        self.entity_tree.bind("<<TreeviewSelect>>",self.select_entity)
        edit=tk.LabelFrame(ent_top,text="Editar posición y rotación",bg="#101522",fg="#dce5f2",
                           padx=10,pady=8)
        edit.pack(fill="x",pady=(10,0))
        self.entity_vars={}
        for idx,key in enumerate(("x","y","z","rotation")):
            tk.Label(edit,text=key.upper(),bg="#101522",fg="#dce5f2").grid(row=0,column=idx*2,sticky="w",padx=(0,5))
            var=tk.StringVar()
            self.entity_vars[key]=var
            tk.Entry(edit,textvariable=var,bg="#151e2e",fg="white",insertbackground="white",
                     relief="flat",width=18).grid(row=0,column=idx*2+1,sticky="ew",padx=(0,12),ipady=5)
        ttk.Button(edit,text="Aplicar a entidad",command=self.apply_entity_edit).grid(row=0,column=8,padx=6)
        ttk.Button(edit,text="Guardar XML modificado",command=self.save_entity_xml).grid(row=0,column=9,padx=6)
        tk.Label(ent_top,text="Nota: edita XML exportados; no modifica directamente YMAP binarios. Guarda una copia antes de reemplazar el mapa.",
                 bg="#101522",fg="#91a5bf").pack(anchor="w",pady=(8,0))

        recovery_frame=tk.Frame(self.tab_recovery,bg="#101522")
        recovery_frame.pack(fill="both",expand=True,padx=12,pady=12)
        tk.Label(recovery_frame,text="CENTRO DE RECUPERACIÓN Y CONSERVACIÓN",
                 bg="#101522",fg="white",font=("Segoe UI",12,"bold")).pack(anchor="w")
        tk.Label(recovery_frame,text="Analiza cada archivo, detecta indicadores de protección, revisa exclusiones del manifiesto y prepara un informe verificable.",
                 bg="#101522",fg="#91a5bf",wraplength=980,justify="left").pack(anchor="w",pady=(3,8))
        self.recovery_stage=tk.StringVar(value="En espera de un recurso")
        tk.Label(recovery_frame,textvariable=self.recovery_stage,bg="#101522",fg="#93c5fd",font=("Segoe UI",10,"bold")).pack(anchor="w")
        self.recovery_progress=ttk.Progressbar(recovery_frame,mode="determinate",maximum=100)
        self.recovery_progress.pack(fill="x",pady=(5,10))
        rec_actions=tk.Frame(recovery_frame,bg="#101522")
        rec_actions.pack(fill="x",pady=(0,8))
        ttk.Button(rec_actions,text="Analizar recurso",command=self.recovery_analyze).pack(side="left",padx=(0,6))
        ttk.Button(rec_actions,text="Exportar informe JSON",command=self.export_recovery_report).pack(side="left",padx=6)
        ttk.Button(rec_actions,text="Crear copia íntegra ZIP",command=self.create_preserved_zip).pack(side="left",padx=6)
        ttk.Button(rec_actions,text="Revisar errores Lua",command=self.lua_preflight).pack(side="left",padx=6)
        ttk.Button(rec_actions,text="Exportar diagnóstico",command=self.export_lua_diagnostics).pack(side="left",padx=6)
        self.recovery_text=tk.Text(recovery_frame,bg="#151e2e",fg="#e8edf7",
            insertbackground="white",wrap="word",font=("Consolas",9),relief="flat",padx=12,pady=12)
        self.recovery_text.pack(fill="both",expand=True)
        self.recovery_report_data=None
        self.lua_diagnostics=[]

        perm_frame=tk.Frame(self.tab_permissions,bg="#101522")
        perm_frame.pack(fill="both",expand=True,padx=14,pady=14)
        tk.Label(perm_frame,text="PERMISOS ACE — CONFIGURACIÓN MANUAL Y OPCIONAL",
                 bg="#101522",fg="white",font=("Segoe UI",12,"bold")).pack(anchor="w")
        tk.Label(perm_frame,text="Edita libremente las líneas que indique la documentación del recurso. El programa nunca las añade automáticamente a server.cfg.",
                 bg="#101522",fg="#91a5bf",wraplength=900,justify="left").pack(anchor="w",pady=(4,10))
        self.permission_hint=tk.Label(perm_frame,text="Tipo de recurso: aún no analizado.",
                 bg="#101522",fg="#93c5fd",font=("Segoe UI",10,"bold"))
        self.permission_hint.pack(anchor="w",pady=(0,8))
        self.permission_editor=tk.Text(perm_frame,bg="#151e2e",fg="#e8edf7",
            insertbackground="white",wrap="none",font=("Consolas",10),relief="flat",
            padx=12,pady=12,height=16)
        self.permission_editor.pack(fill="both",expand=True)
        self.permission_editor.insert("1.0",
            "# Permisos ACE opcionales para scripts FiveM\\n"
            "# Pega aquí únicamente las líneas requeridas por el creador del recurso.\\n"
            "# Ejemplo editable; descomenta y adapta solo si la documentación lo solicita:\\n"
            "# add_ace resource.NOMBRE_RECURSO command.add_ace allow\\n"
            "# add_ace resource.NOMBRE_RECURSO command.remove_ace allow\\n"
            "# add_ace resource.NOMBRE_RECURSO command.add_principal allow\\n"
            "# add_ace resource.NOMBRE_RECURSO command.remove_principal allow\\n"
            "#\\n"
            "# Para mapas/MLO normalmente no se requiere un bloque ACE.\\n")
        perm_actions=tk.Frame(perm_frame,bg="#101522")
        perm_actions.pack(fill="x",pady=(8,0))
        ttk.Button(perm_actions,text="Validar sintaxis básica",command=self.validate_ace_text).pack(side="left",padx=(0,6))
        ttk.Button(perm_actions,text="Guardar como permissions.cfg",command=self.save_ace_file).pack(side="left",padx=6)
        ttk.Button(perm_actions,text="Restablecer ejemplo",command=self.reset_ace_text).pack(side="left",padx=6)
        tk.Label(perm_frame,text="Este editor no asigna administradores ni decide quién recibe permisos: eso lo define el propietario del servidor.",
                 bg="#101522",fg="#91a5bf").pack(anchor="w",pady=(8,0))

    def reset_ace_text(self):
        self.permission_editor.delete("1.0","end")
        self.permission_editor.insert("1.0",
            "# Permisos ACE opcionales para scripts FiveM\\n"
            "# Configura manualmente según la documentación del recurso.\\n"
            "# add_ace resource.NOMBRE_RECURSO command.add_ace allow\\n"
            "# add_ace resource.NOMBRE_RECURSO command.remove_ace allow\\n"
            "# add_ace resource.NOMBRE_RECURSO command.add_principal allow\\n"
            "# add_ace resource.NOMBRE_RECURSO command.remove_principal allow\\n"
            "# En mapas/MLO normalmente no se requiere ACE.\\n")

    def validate_ace_text(self):
        textdata=self.permission_editor.get("1.0","end")
        issues=[]
        for no,line in enumerate(textdata.splitlines(),1):
            code=line.split("#",1)[0].strip()
            if not code: continue
            parts=code.split()
            if parts[0]=="add_ace":
                if len(parts)!=4 or parts[-1] not in ("allow","deny"):
                    issues.append(f"Línea {no}: add_ace debe tener 4 campos: add_ace principal objeto allow|deny")
            elif parts[0] in ("remove_ace",):
                if len(parts)!=4 or parts[-1] not in ("allow","deny"):
                    issues.append(f"Línea {no}: remove_ace debe tener 4 campos y terminar en allow|deny")
            elif parts[0] in ("add_principal","remove_principal"):
                if len(parts)!=3:
                    issues.append(f"Línea {no}: {parts[0]} debe tener 3 campos.")
            elif parts[0] not in ("exec",):
                issues.append(f"Línea {no}: comando no reconocido por el validador ACE básico ({parts[0]}).")
        if issues:
            messagebox.showwarning("Revisión ACE","\\n".join(issues))
        else:
            messagebox.showinfo("Revisión ACE","Sintaxis básica correcta. Esto no confirma que los permisos sean necesarios ni que la política sea segura.")
        return not issues

    def save_ace_file(self):
        content=self.permission_editor.get("1.0","end-1c")
        dest=filedialog.asksaveasfilename(defaultextension=".cfg",initialfile="permissions.cfg",
                                          filetypes=[("CFG","*.cfg"),("Texto","*.txt")])
        if not dest:return
        try:
            with open(dest,"w",encoding="utf-8",newline="\\n") as f:f.write(content)
            messagebox.showinfo("Guardado",f"Se guardó el bloque editable en:\\n{dest}\\n\\nInclúyelo en server.cfg con exec permissions.cfg solo si corresponde.")
        except Exception as e:messagebox.showerror("Error",str(e))

    def _update_permission_hint(self):
        if not hasattr(self,"permission_hint"): return
        if not self.workdir:
            self.permission_hint.config(text="Tipo de recurso: aún no analizado.")
            return
        manifest=None
        for candidate in ("fxmanifest.lua","__resource.lua"):
            pth=os.path.join(self.workdir,candidate)
            if os.path.isfile(pth): manifest=pth; break
        if not manifest:
            self.permission_hint.config(text="Tipo no determinado: no se encontró manifest.")
            return
        try: data=open(manifest,"r",encoding="utf-8",errors="ignore").read()
        except: data=""
        is_map=bool(re.search(r"this_is_a_map\\s*['\\\"]?\\s*yes",data,re.I))
        has_scripts=bool(re.search(r"(client|server|shared)_script\\s*['\\\"]",data,re.I))
        if is_map and not has_scripts:
            self.permission_hint.config(text="Tipo detectado: MAPA/MLO — normalmente no necesita permisos ACE. Editor disponible, pero no se aplicará nada.")
        elif has_scripts:
            self.permission_hint.config(text="Tipo detectado: SCRIPT — revisa la documentación y decide manualmente si necesita ACE.")
        elif is_map:
            self.permission_hint.config(text="Tipo detectado: MAPA/MLO — normalmente no necesita permisos ACE.")
        else:
            self.permission_hint.config(text="Tipo detectado: recurso mixto o no identificado — ACE queda opcional y editable.")

    def load_zip(self):
        p = filedialog.askopenfilename(filetypes=[("Archivos ZIP","*.zip"),("Todos","*.*")])
        if not p: return
        self.zip_path = p
        self.workdir = None
        self.scan_zip()

    def scan_zip(self):
        self.tree.delete(*self.tree.get_children())
        self.report.delete("1.0","end")
        self.maps.delete("1.0","end")
        try:
            with zipfile.ZipFile(self.zip_path) as z:
                names = [i for i in z.infolist() if not i.is_dir()]
                total = sum(i.file_size for i in names)
                fxap = []
                lua = []
                counts = {}
                for i in names:
                    ext = Path(i.filename).suffix.lower()
                    counts[ext] = counts.get(ext,0)+1
                    if ext == ".lua":
                        lua.append(i.filename)
                        try:
                            with z.open(i) as f: sig = f.read(4)
                            if sig == b"FXAP": fxap.append(i.filename)
                        except: pass
                    self.tree.insert("", "end", text=i.filename,
                                     values=(self.fmt_size(i.file_size), ext or "archivo"))
                self.report.insert("end", f"RECURSO: {os.path.basename(self.zip_path)}\n")
                self.report.insert("end", f"Archivos: {len(names)} | Tamaño descomprimido: {self.fmt_size(total)}\n\n")
                self.report.insert("end", "TIPOS DE ARCHIVO\n")
                for ext,n in sorted(counts.items(), key=lambda x:x[0]): self.report.insert("end", f"  {ext or '[sin extensión]'}: {n}\n")
                self.report.insert("end", f"\nScripts Lua encontrados: {len(lua)}\n")
                for f in lua[:80]: self.report.insert("end", f"  • {f}\n")
                if fxap:
                    self.report.insert("end", "\nPROTECCIÓN DETECTADA\n")
                    self.report.insert("end", "Se detectó la firma FXAP en estos Lua:\n")
                    for f in fxap: self.report.insert("end", f"  • {f}\n")
                    self.report.insert("end", "\nEstos archivos están protegidos por CFX Asset Escrow. Esta herramienta no elimina ni evade esa protección. Solicita al creador una copia fuente o acceso/autorización oficial.\n")
                else:
                    self.report.insert("end", "\nNo se detectó la firma FXAP en los primeros bytes de los archivos Lua inspeccionados. Esto no garantiza que todos los archivos sean editables.\n")
                self.status.set(f"{len(names)} archivos analizados.")
                self._map_report_from_zip(z)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _map_report_from_zip(self,z):
        self.maps.delete("1.0","end")
        self.maps.insert("end","INVENTARIO DE MAPAS / STREAM\n\n")
        coords = []
        asset_counts = {}
        text_files = []
        for i in z.infolist():
            if i.is_dir(): continue
            ext=Path(i.filename).suffix.lower()
            if ext in MAP_EXT:
                asset_counts[ext] = asset_counts.get(ext,0)+1
                self.maps.insert("end",f"{ext.upper():6}  {i.filename}  ({self.fmt_size(i.file_size)})\n")
            if ext in TEXT_EXT and i.file_size < 3_000_000:
                text_files.append(i.filename)
                try:
                    data=z.read(i.filename).decode("utf-8",errors="ignore")
                    coords.extend(self.find_coords(data, i.filename))
                except: pass
        self.maps.insert("end","\nRESUMEN DE ARCHIVOS\n")
        if asset_counts:
            for ext,n in sorted(asset_counts.items()):
                self.maps.insert("end",f"  {ext}: {n}\n")
        else:
            self.maps.insert("end","  No se detectaron archivos de mapa/stream conocidos.\n")
        self.maps.insert("end",f"\nArchivos de texto revisados: {len(text_files)}\n")
        self.maps.insert("end","\nCOORDENADAS DETECTADAS EN TEXTO\n")
        self.coords_data = coords
        if coords:
            for row in coords[:500]:
                self.maps.insert("end",f"{row['x']}, {row['y']}, {row['z']}  [{row['pattern']}]  {row['file']}\n")
            if len(coords)>500:
                self.maps.insert("end",f"\n... y {len(coords)-500} coordenadas más. Exporta el CSV para verlas todas.\n")
        else:
            self.maps.insert("end","No se encontraron coordenadas escritas en texto.\n")
        self.maps.insert("end","\nNOTA: YMAP/YTYP/YBN/YDR/YDD/YTD/YFT suelen ser datos binarios. Este inventario no los convierte a formato editable; para eso se requiere una herramienta compatible de edición de assets GTA V.\n")

    def find_coords(self, data, filename):
        found=[]
        patterns=[
            ("vector3", r"vector3\s*\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)"),
            ("vector4", r"vector4\s*\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)"),
            ("vec3", r"vec3\s*\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)"),
            ("xyz", r"""['"]?x['"]?\s*[:=]\s*(-?\d+(?:\.\d+)?)[\s\S]{0,120}?['"]?y['"]?\s*[:=]\s*(-?\d+(?:\.\d+)?)[\s\S]{0,120}?['"]?z['"]?\s*[:=]\s*(-?\d+(?:\.\d+)?)"""),
            ("triple", r"(?<![\w.])(-?\d{1,3}\.\d{3,})\s*,\s*(-?\d{1,3}\.\d{3,})\s*,\s*(-?\d{1,3}\.\d{3,})(?![\w.])")
        ]
        for label,pat in patterns:
            for m in re.finditer(pat,data,re.I):
                vals=m.groups()[:3]
                try:
                    x,y,zv=[float(v) for v in vals]
                    # Filter obvious non-world-coordinate values
                    if abs(x)>20000 or abs(y)>20000 or abs(zv)>10000: continue
                    line=data.count("\n",0,m.start())+1
                    found.append({"x":x,"y":y,"z":zv,"file":filename,"line":line,"pattern":label})
                except: pass
        # Deduplicate identical coordinates in same file
        seen=set(); unique=[]
        for r in found:
            k=(r["x"],r["y"],r["z"],r["file"])
            if k not in seen: seen.add(k); unique.append(r)
        return unique

    def export_coords(self):
        coords=getattr(self,"coords_data",[])
        if not coords:
            messagebox.showinfo("Coordenadas","Primero analiza un ZIP o carpeta que contenga coordenadas en archivos de texto.")
            return
        dest=filedialog.asksaveasfilename(defaultextension=".csv",initialfile="coordenadas_fivem.csv",
                                          filetypes=[("CSV","*.csv")])
        if not dest:return
        try:
            with open(dest,"w",newline="",encoding="utf-8-sig") as f:
                w=csv.DictWriter(f,fieldnames=["x","y","z","file","line","pattern"])
                w.writeheader(); w.writerows(coords)
            messagebox.showinfo("Exportación lista",f"Se exportaron {len(coords)} coordenadas:\n{dest}")
        except Exception as e: messagebox.showerror("Error",str(e))

    def extract(self):
        if not self.zip_path:
            messagebox.showinfo("Aviso","Primero carga un ZIP."); return
        dest=filedialog.askdirectory(title="Carpeta de destino")
        if not dest:return
        try:
            out=os.path.join(dest,Path(self.zip_path).stem+"_extraido")
            os.makedirs(out,exist_ok=True)
            extracted=0; skipped=0; protected=0
            with zipfile.ZipFile(self.zip_path) as z:
                for info in z.infolist():
                    if info.is_dir(): continue
                    name=info.filename.replace("\\","/")
                    parts=Path(name).parts
                    # Reject absolute, parent traversal and Windows drive paths.
                    if name.startswith("/") or name.startswith("\\\\") or ".." in parts or (parts and ":" in parts[0]):
                        skipped+=1; continue
                    target=os.path.abspath(os.path.join(out,*parts))
                    if os.path.commonpath([os.path.abspath(out),target]) != os.path.abspath(out):
                        skipped+=1; continue
                    os.makedirs(os.path.dirname(target),exist_ok=True)
                    with z.open(info) as src, open(target,"wb") as dst:
                        first=src.read(4)
                        if first==b"FXAP": protected+=1
                        dst.write(first)
                        shutil.copyfileobj(src,dst)
                    extracted+=1
            self.workdir=out
            self.status.set(f"Extraídos {extracted}; FXAP conservados {protected}; rutas inseguras omitidas {skipped}.")
            messagebox.showinfo("Extracción terminada",
                f"Carpeta:\\n{out}\\n\\nArchivos extraídos: {extracted}\\nArchivos FXAP conservados sin modificar: {protected}\\nRutas inseguras omitidas: {skipped}")
            self.scan_folder(out)
            self._update_permission_hint()
        except Exception as e: messagebox.showerror("Error",str(e))

    def open_folder(self):
        p=filedialog.askdirectory()
        if p: self.workdir=p; self.scan_folder(p)

    def scan_folder(self,root):
        root_path = root
        self.tree.delete(*self.tree.get_children())
        self.report.delete("1.0","end")
        count=0
        for base,dirs,files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in (".git","__pycache__")]
            for fn in files:
                p=os.path.join(base,fn); rel=os.path.relpath(p,root); ext=Path(fn).suffix.lower()
                try:size=os.path.getsize(p)
                except:size=0
                self.tree.insert("","end",text=rel,values=(self.fmt_size(size),ext or "archivo")); count+=1
        self.report.insert("end",f"CARPETA: {root_path}\nArchivos: {count}\n\nAbre un archivo con doble clic para editarlo.\n")
        self.status.set(f"{count} archivos en carpeta.")
        self._update_permission_hint()
        self.coords_data = []
        self.maps.delete("1.0","end")
        self.maps.insert("end","INVENTARIO DE MAPAS / STREAM\n\n")
        asset_counts = {}
        for walk_root, dirs, files in os.walk(root_path):
            for fn in files:
                full=os.path.join(walk_root,fn); ext=Path(fn).suffix.lower()
                if ext in MAP_EXT:
                    asset_counts[ext]=asset_counts.get(ext,0)+1
                    self.maps.insert("end",f"{ext.upper():6}  {os.path.relpath(full,self.workdir)}\n")
                if ext in TEXT_EXT:
                    try:
                        if os.path.getsize(full) <= 3_000_000:
                            with open(full,"r",encoding="utf-8",errors="ignore") as f:
                                self.coords_data.extend(self.find_coords(f.read(),os.path.relpath(full,self.workdir)))
                    except: pass
        self.maps.insert("end","\nRESUMEN\n")
        for ext,n in sorted(asset_counts.items()):
            self.maps.insert("end",f"  {ext}: {n}\n")
        self.maps.insert("end",f"\nCoordenadas detectadas: {len(self.coords_data)}\n")
        for row in self.coords_data[:500]:
            self.maps.insert("end",f"{row['x']}, {row['y']}, {row['z']}  [{row['pattern']}]  {row['file']}:{row['line']}\n")
        self.maps.insert("end","\nPara inspección de entidades: exporta YMAP a XML con una herramienta compatible y coloca el XML en la carpeta del recurso. Luego usa «Exportar entidades CSV».\n")
        self._load_entity_rows()

    def open_selected(self,event=None):
        sel=self.tree.selection()
        if not sel:return
        rel=self.tree.item(sel[0],"text")
        if self.zip_path and not self.workdir:
            try:
                with zipfile.ZipFile(self.zip_path) as z:
                    raw=z.read(rel)
                if raw[:4]==b"FXAP":
                    messagebox.showwarning("Archivo protegido","Este Lua está protegido por CFX Asset Escrow y no se puede abrir como texto.")
                    return
                content=raw.decode("utf-8")
                self.current_file=("zip",rel)
            except Exception as e:
                messagebox.showinfo("No editable","No se pudo abrir como texto. Puede ser un archivo binario o protegido."); return
        elif self.workdir:
            p=os.path.join(self.workdir,rel)
            try:
                if os.path.getsize(p)>4_000_000: raise ValueError("Archivo demasiado grande para el editor.")
                raw=open(p,"rb").read()
                if raw[:4]==b"FXAP": raise ValueError("Firma FXAP: archivo protegido.")
                content=raw.decode("utf-8")
                self.current_file=("disk",p)
            except Exception as e:
                messagebox.showinfo("No editable",str(e)); return
        else:return
        self.editor.delete("1.0","end"); self.editor.insert("1.0",content)
        self.tabs.select(self.tab_editor)
        self.status.set(f"Editando: {rel}")

    def save_file(self):
        if not self.current_file:
            messagebox.showinfo("Guardar","Abre primero un archivo de texto."); return
        mode,path=self.current_file
        if mode=="zip":
            messagebox.showinfo("Guardar","Los ZIP no se modifican directamente. Extrae los archivos accesibles y abre la carpeta para guardar tus cambios."); return
        try:
            with open(path,"w",encoding="utf-8",newline="") as f:f.write(self.editor.get("1.0","end-1c"))
            self.status.set("Archivo guardado.")
            messagebox.showinfo("Guardado",f"Se guardó:\n{path}")
        except Exception as e:messagebox.showerror("Error",str(e))

    def lua_preflight(self):
        """Static checks only: never claims to prove runtime compatibility."""
        if not self.workdir:
            messagebox.showinfo("Revisión Lua","Extrae los archivos accesibles o abre una carpeta primero.")
            return
        findings=[]
        for root,dirs,files in os.walk(self.workdir):
            dirs[:] = [d for d in dirs if d not in (".git","__pycache__")]
            for fn in files:
                if not fn.lower().endswith(".lua"): continue
                full=os.path.join(root,fn)
                try:
                    if os.path.getsize(full)>8_000_000: continue
                    with open(full,"rb") as f: raw=f.read()
                    if raw[:4]==b"FXAP":
                        findings.append({"file":os.path.relpath(full,self.workdir),"line":1,
                            "severity":"BLOQUEADO","code":"FXAP_PROTECTED",
                            "detail":"Archivo protegido. No se analiza ni modifica su contenido."})
                        continue
                    textdata=raw.decode("utf-8")
                    lines=textdata.splitlines()
                    for i,line in enumerate(lines,1):
                        # Catch both direct and decompiler-style split references:
                        # local = promise; local = local.new; local = condition and local
                        split_promise = False
                        if i >= 2 and re.search(r"=\s*promise\s*$", lines[i-2].strip(), re.I):
                            var_match = re.search(r"^\s*(\w+)\s*=\s*(\w+)\.new\s*$", line, re.I)
                            split_promise = bool(var_match and var_match.group(1) == var_match.group(2))
                        if split_promise:
                            findings.append({"file":os.path.relpath(full,self.workdir),"line":i,
                                "severity":"ERROR_PROBABLE","code":"PROMISE_NEW_NOT_INVOKED",
                                "detail":"Patrón similar a Luxu Admin: promise.new se guarda como función sin ejecutarse. En el flujo que espera una instancia, revisa si corresponde llamar promise.new()."})
                        # Common bug: assigning promise.new function itself instead of calling it.
                        if re.search(r"=\s*promise\.new\s*$",line.strip(),re.I) or re.search(r"=\s*\w+\.new\s*$",line.strip(),re.I):
                            findings.append({"file":os.path.relpath(full,self.workdir),"line":i,
                                "severity":"ADVERTENCIA","code":"POSSIBLE_PROMISE_CONSTRUCTOR_REFERENCE",
                                "detail":"Posible referencia a constructor .new sin llamada (). Verifica que se cree una instancia Promise."})
                        if re.search(r"\bCitizen\.Await\s*\(\s*\w+\s*\)",line) and i>1:
                            prev=lines[i-2]
                            if re.search(r"\bpromise\.new\s*$",prev.strip(),re.I):
                                findings.append({"file":os.path.relpath(full,self.workdir),"line":i,
                                    "severity":"ERROR_PROBABLE","code":"AWAIT_FUNCTION_NOT_PROMISE",
                                    "detail":"Citizen.Await parece recibir una función/constructor en vez de una instancia Promise."})
                        if "GetPlayer(" in line and "QBCore" in line:
                            findings.append({"file":os.path.relpath(full,self.workdir),"line":i,
                                "severity":"REVISION","code":"FRAMEWORK_API_REVIEW",
                                "detail":"Revisar compatibilidad de API GetPlayer con la versión/framework Qbox instalado."})
                except UnicodeDecodeError:
                    findings.append({"file":os.path.relpath(full,self.workdir),"line":1,
                        "severity":"NO_TEXTO","code":"NON_UTF8_LUA",
                        "detail":"El archivo Lua no parece texto UTF-8; puede ser binario, empaquetado u ofuscado."})
                except Exception as e:
                    findings.append({"file":os.path.relpath(full,self.workdir),"line":1,
                        "severity":"ERROR_LECTURA","code":"READ_ERROR","detail":str(e)})
        self.lua_diagnostics=findings
        self.recovery_text.delete("1.0","end")
        self.recovery_text.insert("end","REVISIÓN ESTÁTICA DE LUA / COMPATIBILIDAD\\n\\n")
        self.recovery_text.insert("end",f"Hallazgos: {len(findings)}\\n")
        self.recovery_text.insert("end","Esta revisión busca patrones conocidos; no ejecuta el recurso ni garantiza ausencia de errores en FiveM.\\n\\n")
        if not findings:self.recovery_text.insert("end","No se encontraron patrones de esta lista. Aún se requiere prueba en servidor de desarrollo.\\n")
        for f in findings:
            self.recovery_text.insert("end",f"[{f['severity']}] {f['code']}\\n  {f['file']}:{f['line']}\\n  {f['detail']}\\n\\n")
        self.tabs.select(self.tab_recovery)
        self.status.set(f"Revisión Lua: {len(findings)} hallazgos.")

    def export_lua_diagnostics(self):
        if not self.lua_diagnostics:
            messagebox.showinfo("Diagnóstico","Ejecuta primero Revisar errores Lua.")
            return
        dest=filedialog.asksaveasfilename(defaultextension=".json",initialfile="diagnostico_lua.json",
                                          filetypes=[("JSON","*.json")])
        if not dest:return
        try:
            with open(dest,"w",encoding="utf-8") as f:
                json.dump({"findings":self.lua_diagnostics,
                    "scope":"Static pattern checks only; runtime validation required."},f,ensure_ascii=False,indent=2)
            messagebox.showinfo("Exportado",dest)
        except Exception as e:messagebox.showerror("Error",str(e))

    def recovery_analyze(self):
        """Inspección estática y no destructiva. No descifra ni modifica contenido protegido."""
        if not self.zip_path and not self.workdir:
            messagebox.showinfo("Análisis", "Carga un ZIP o abre una carpeta primero.")
            return
        source = self.zip_path if self.zip_path else self.workdir
        records=[]
        summary={"files":0,"bytes":0,"fxap_markers":0,"lua":0,"binary_assets":0,
                 "text":0,"other":0,"unsafe":0,"manifest_ignore_patterns":0}
        manifest_text=[]
        self.recovery_progress["value"]=0
        self.recovery_stage.set("1/4 · Preparando inventario de archivos...")
        self.update_idletasks()
        try:
            if self.zip_path:
                with zipfile.ZipFile(self.zip_path) as z:
                    infos=[i for i in z.infolist() if not i.is_dir()]
                    total=max(len(infos),1)
                    for idx,info in enumerate(infos,1):
                        name=info.filename.replace("\\","/")
                        parts=Path(name).parts
                        unsafe=(name.startswith("/") or name.startswith("\\\\") or ".." in parts or (parts and ":" in parts[0]))
                        if unsafe:
                            summary["unsafe"]+=1
                            records.append({"path":name,"size":info.file_size,"status":"RUTA_INSEGURA","detail":"No se inspeccionó por seguridad.","sha256":None})
                            continue
                        with z.open(info) as f:
                            head=f.read(16)
                            if Path(name).name.lower()=="fxmanifest.lua" or Path(name).name.lower()=="__resource.lua":
                                raw=head+f.read()
                                manifest_text.append((name,raw.decode("utf-8","replace")))
                        ext=Path(name).suffix.lower()
                        is_fxap=(head[:4]==b"FXAP" or ext==".fxap")
                        if is_fxap:
                            status="INDICADOR_FXAP"
                            detail="Marcador/archivo FXAP detectado; no se ha determinado ni recuperado el contenido cifrado."
                            summary["fxap_markers"]+=1
                        elif ext==".lua":
                            status="LUA_POR_INSPECCIONAR"
                            detail="Archivo Lua localizado. La extensión por sí sola no determina si está protegido u ofuscado."
                            summary["lua"]+=1
                        elif ext in MAP_EXT:
                            status="ASSET_BINARIO"
                            detail="Formato de asset identificado; la extensión no demuestra por sí sola protección."
                            summary["binary_assets"]+=1
                        elif ext in TEXT_EXT:
                            status="TEXTO_INSPECCIONABLE"
                            detail="Archivo de texto; se puede inspeccionar si su contenido es legible."
                            summary["text"]+=1
                        else:
                            status="FORMATO_NO_CLASIFICADO"
                            detail="Formato inventariado; requiere un analizador específico para identificar su contenido."
                            summary["other"]+=1
                        summary["files"]+=1; summary["bytes"]+=info.file_size
                        records.append({"path":name,"size":info.file_size,"status":status,"detail":detail,"sha256":None})
                        if idx % 20 == 0 or idx==total:
                            self.recovery_progress["value"]=min(65, int(idx/total*65))
                            self.recovery_stage.set(f"2/4 · Analizando archivos: {idx}/{total}")
                            self.update_idletasks()
            else:
                all_files=[]
                for root,dirs,files in os.walk(self.workdir):
                    dirs[:]=[d for d in dirs if d not in (".git","__pycache__")]
                    for fn in files: all_files.append(os.path.join(root,fn))
                total=max(len(all_files),1)
                for idx,full in enumerate(all_files,1):
                    name=os.path.relpath(full,self.workdir).replace("\\","/")
                    with open(full,"rb") as f:
                        head=f.read(16)
                        if Path(name).name.lower() in ("fxmanifest.lua","__resource.lua"):
                            manifest_text.append((name,(head+f.read()).decode("utf-8","replace")))
                    ext=Path(name).suffix.lower(); size=os.path.getsize(full)
                    is_fxap=(head[:4]==b"FXAP" or ext==".fxap")
                    if is_fxap: status="INDICADOR_FXAP"; detail="Marcador/archivo FXAP detectado; no se ha recuperado contenido."; summary["fxap_markers"]+=1
                    elif ext==".lua": status="LUA_POR_INSPECCIONAR"; detail="La extensión no determina por sí sola protección u ofuscación."; summary["lua"]+=1
                    elif ext in MAP_EXT: status="ASSET_BINARIO"; detail="Formato de asset identificado; protección no confirmada por extensión."; summary["binary_assets"]+=1
                    elif ext in TEXT_EXT: status="TEXTO_INSPECCIONABLE"; detail="Archivo de texto potencialmente inspeccionable."; summary["text"]+=1
                    else: status="FORMATO_NO_CLASIFICADO"; detail="Requiere analizador específico."; summary["other"]+=1
                    summary["files"]+=1; summary["bytes"]+=size
                    records.append({"path":name,"size":size,"status":status,"detail":detail,"sha256":None})
                    if idx % 20 == 0 or idx==total:
                        self.recovery_progress["value"]=min(65,int(idx/total*65)); self.recovery_stage.set(f"2/4 · Analizando archivos: {idx}/{total}"); self.update_idletasks()
            self.recovery_stage.set("3/4 · Revisando exclusiones declaradas en manifiestos...")
            self.recovery_progress["value"]=78; self.update_idletasks()
            ignore=[]
            for mpath,txt in manifest_text:
                for match in re.finditer(r"escrow_ignore\s*\{([^}]*)\}",txt,re.I|re.S):
                    body=match.group(1)
                    ignore.extend(re.findall(r"['\"]([^'\"]+)['\"]",body))
            summary["manifest_ignore_patterns"]=len(ignore)
            for r in records:
                if any(fnmatch.fnmatch(r["path"],pat) or fnmatch.fnmatch(Path(r["path"]).name,pat) for pat in ignore):
                    r["manifest_note"]="Coincide con un patrón escrow_ignore declarado; comprobar el patrón y la ruta en el manifiesto."
            self.recovery_stage.set("4/4 · Preparando informe y verificando inventario...")
            self.recovery_progress["value"]=94; self.update_idletasks()
            self.recovery_report_data={"source":source,"summary":summary,"escrow_ignore_patterns":ignore,"files":records,
                "scope":"Inspección estática no destructiva. No descifra, no elimina FXAP y no confirma criptográficamente protección por extensión.",
                "next_step":"Para recuperar contenido protegido se necesita una exportación/fuente de recuperación autorizada del creador o proveedor. Este informe identifica candidatos y conserva los originales."}
            self.recovery_text.delete("1.0","end")
            self.recovery_text.insert("end","INFORME DE ANÁLISIS INTELIGENTE\n")
            self.recovery_text.insert("end",f"Origen: {source}\nArchivos: {summary['files']} · Tamaño: {self.fmt_size(summary['bytes'])}\n")
            self.recovery_text.insert("end",f"Indicadores FXAP: {summary['fxap_markers']}\nArchivos Lua: {summary['lua']}\nAssets binarios: {summary['binary_assets']}\nTexto: {summary['text']}\nOtros: {summary['other']}\nRutas inseguras: {summary['unsafe']}\nPatrones escrow_ignore: {len(ignore)}\n")
            if ignore:
                self.recovery_text.insert("end","\nPATRONES escrow_ignore DECLARADOS\n")
                for pat in ignore: self.recovery_text.insert("end",f"  • {pat}\n")
            self.recovery_text.insert("end","\nDETALLE DE ARCHIVOS\n")
            for r in records:
                self.recovery_text.insert("end",f"[{r['status']}] {r['path']} ({self.fmt_size(r['size'])})\n  {r['detail']}\n")
                if r.get("manifest_note"): self.recovery_text.insert("end",f"  {r['manifest_note']}\n")
            self.recovery_text.insert("end","\nIMPORTANTE: detectar FXAP o una extensión compatible no revela por sí solo qué contenido está cifrado. Los archivos originales no se modificaron. La aplicación no elimina marcadores ni simula una recuperación.\n")
            self.recovery_progress["value"]=100; self.recovery_stage.set("Análisis terminado · No se modificó ningún archivo")
            self.tabs.select(self.tab_recovery); self.status.set("Análisis inteligente terminado.")
        except Exception as e:
            self.recovery_stage.set("El análisis encontró un error")
            messagebox.showerror("Error de análisis",str(e))

    def export_recovery_report(self):
        if not self.recovery_report_data:
            messagebox.showinfo("Informe","Primero analiza un recurso.")
            return
        dest=filedialog.asksaveasfilename(defaultextension=".json",initialfile="informe_recuperacion.json",
                                          filetypes=[("JSON","*.json")])
        if not dest:return
        try:
            with open(dest,"w",encoding="utf-8") as f:
                json.dump(self.recovery_report_data,f,ensure_ascii=False,indent=2)
            messagebox.showinfo("Informe exportado",dest)
        except Exception as e:messagebox.showerror("Error",str(e))

    def create_preserved_zip(self):
        if not self.zip_path:
            messagebox.showinfo("Copia íntegra","Carga primero un ZIP original.")
            return
        dest=filedialog.asksaveasfilename(defaultextension=".zip",
            initialfile=Path(self.zip_path).stem+"_copia_integra.zip",
            filetypes=[("ZIP","*.zip")])
        if not dest:return
        try:
            # Copy bytes exactly; no re-compression or rewriting of protected content.
            shutil.copy2(self.zip_path,dest)
            with zipfile.ZipFile(dest,"r") as z:
                if z.testzip() is not None: raise ValueError("La verificación interna del ZIP ha fallado.")
            messagebox.showinfo("Copia creada",f"Se creó y verificó una copia íntegra:\\n{dest}")
        except Exception as e:messagebox.showerror("Error",str(e))

    def audit_resource(self):
        if not self.workdir:
            messagebox.showinfo("Auditoría", "Primero extrae los archivos accesibles o abre una carpeta del recurso.")
            return
        root_dir=os.path.abspath(self.workdir)
        manifest=os.path.join(root_dir,"fxmanifest.lua")
        legacy=os.path.join(root_dir,"__resource.lua")
        report=[]
        report.append("AUDITORÍA DEL RECURSO FIVE M\n")
        report.append(f"Carpeta: {root_dir}\n")
        if os.path.isfile(manifest):
            mf=manifest
            report.append("Manifest: fxmanifest.lua encontrado\n")
        elif os.path.isfile(legacy):
            mf=legacy
            report.append("Manifest: __resource.lua (formato antiguo) encontrado\n")
        else:
            mf=None
            report.append("ADVERTENCIA: no se encontró fxmanifest.lua ni __resource.lua\n")
        all_files=set()
        for r,ds,fs in os.walk(root_dir):
            for fn in fs:
                all_files.add(os.path.relpath(os.path.join(r,fn),root_dir).replace("\\","/").lower())
        if mf:
            try:
                txt=open(mf,"r",encoding="utf-8",errors="ignore").read()
                report.append("\nCONFIGURACIÓN DETECTADA\n")
                for key in ("fx_version","game","lua54","this_is_a_map","use_experimental_fxv2_oal"):
                    m=re.search(r"""^\s*"""+key+r"""\s+['"]?([^'"\n]+)['"]?""",txt,re.I|re.M)
                    if m: report.append(f"  {key}: {m.group(1).strip()}\n")
                for kind,pat in [
                    ("scripts",r"""(?:client_script|server_script|shared_script)\s+['"]([^'"]+)['"]"""),
                    ("archivos",r"""files\s*\{([\s\S]*?)\}"""),
                    ("data_file",r"""data_file\s+['"]([^'"]+)['"]\s*,\s*['"]([^'"]+)['"]"""),
                    ("dependencias",r"""dependency\s+['"]([^'"]+)['"]""")
                ]:
                    report.append(f"\n{kind.upper()}\n")
                    matches=re.findall(pat,txt,re.I)
                    if kind=="archivos":
                        vals=[]
                        for block in matches:
                            vals.extend(re.findall(r"""['"]([^'"]+)['"]""",block))
                        matches=vals
                    if not matches: report.append("  (ninguno detectado)\n")
                    for item in matches:
                        if isinstance(item,tuple):
                            path=item[1]
                            report.append(f"  {item[0]} -> {path}")
                        else:
                            path=item
                            report.append(f"  {item}")
                        if isinstance(item,tuple): report.append("  ")
                        # Resolve simple literal paths only; globs are not missing-file errors.
                        if isinstance(path,str) and not any(ch in path for ch in "*?{}"):
                            normalized=path.replace("\\","/").lstrip("./").lower()
                            if normalized not in all_files and not normalized.startswith("@"):
                                report.append("  [NO ENCONTRADO]")
                        report.append("\n")
                report.append("\nESCROW_IGNORE\n")
                escrow=re.search(r"""escrow_ignore\s*\{([\s\S]*?)\}""",txt,re.I)
                if escrow:
                    for v in re.findall(r"""['"]([^'"]+)['"]""",escrow.group(1)):
                        report.append(f"  {v}\n")
                else: report.append("  No se encontró bloque escrow_ignore.\n")
            except Exception as e: report.append(f"\nNo se pudo leer manifest: {e}\n")
        self.report.delete("1.0","end")
        self.report.insert("end","".join(report))
        self.tabs.select(self.tab_report)
        self.status.set("Auditoría completada.")

    @staticmethod
    def _xml_child(node, name):
        for child in list(node):
            if child.tag.split("}")[-1].lower() == name.lower():
                return child
        return None

    @staticmethod
    def _xml_vector_values(element, count=3):
        if element is None:
            return None
        keys=("x","y","z","w")
        vals=[]
        for key in keys[:count]:
            if key in element.attrib:
                vals.append(element.attrib[key])
            else:
                child=Studio._xml_child(element,key)
                if child is not None and child.text:
                    vals.append(child.text.strip())
        if len(vals)>=count:
            try: return [float(v) for v in vals[:count]]
            except: pass
        raw=" ".join([element.text or ""] + [v for v in element.attrib.values()])
        nums=re.findall(r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?",raw)
        if len(nums)>=count:
            try:return [float(v) for v in nums[:count]]
            except: pass
        return None

    @staticmethod
    def _xml_set_vector(element, values):
        keys=("x","y","z","w")
        if element is None:
            return False
        nested=[Studio._xml_child(element,k) for k in keys[:len(values)]]
        if all(child is not None for child in nested):
            for child,value in zip(nested,values):
                child.text=f"{value:g}"
            return True
        if all(k in element.attrib for k in keys[:len(values)]):
            for k,value in zip(keys,values):
                element.set(k,f"{value:g}")
            return True
        element.text=" ".join(f"{v:g}" for v in values)
        return True

    def _load_entity_rows(self):
        self.entities_data=[]
        self.xml_trees={}
        if not self.workdir:return
        for root,dirs,files in os.walk(self.workdir):
            dirs[:] = [d for d in dirs if d not in (".git","__pycache__")]
            for fn in files:
                if not fn.lower().endswith(".xml"): continue
                full=os.path.join(root,fn)
                try:
                    if os.path.getsize(full)>20_000_000: continue
                    tree=ET.parse(full)
                    self.xml_trees[full]=tree
                    for node in tree.iter():
                        tag=node.tag.split("}")[-1].lower()
                        if tag not in ("item","centitydef","mapdata"): continue
                        archetype=node.attrib.get("archetypeName") or node.attrib.get("name") or ""
                        arch_el=self._xml_child(node,"archetypeName")
                        if not archetype and arch_el is not None:
                            archetype=(arch_el.text or "").strip()
                        pos_el=self._xml_child(node,"position")
                        pos_attr=node.attrib.get("position")
                        pos=self._xml_vector_values(pos_el,3) if pos_el is not None else None
                        if pos is None and pos_attr:
                            nums=re.findall(r"-?\d+(?:\.\d+)?",pos_attr)
                            if len(nums)>=3: pos=[float(v) for v in nums[:3]]
                        if pos is None: continue
                        rot_el=self._xml_child(node,"rotation")
                        rot_attr=node.attrib.get("rotation","")
                        rot_vals=self._xml_vector_values(rot_el,4) if rot_el is not None else None
                        rot_text=(", ".join(f"{v:g}" for v in rot_vals) if rot_vals else rot_attr)
                        self.entities_data.append({
                            "name":archetype,"x":pos[0],"y":pos[1],"z":pos[2],
                            "rotation":rot_text,"file":os.path.relpath(full,self.workdir),
                            "_node":node,"_path":full,"_pos_el":pos_el,"_rot_el":rot_el,
                            "_pos_attr":pos_attr is not None,"_rot_attr":rot_attr is not None
                        })
                except Exception: pass
        self.refresh_entity_table()
        return self.entities_data

    def refresh_entity_table(self):
        if not hasattr(self,"entity_tree"): return
        self.entity_tree.delete(*self.entity_tree.get_children())
        for i,row in enumerate(self.entities_data):
            self.entity_tree.insert("","end",iid=str(i),text=row["name"] or "(sin nombre)",
                values=(row["x"],row["y"],row["z"],row["file"]))

    def select_entity(self,event=None):
        sel=self.entity_tree.selection()
        if not sel:return
        idx=int(sel[0])
        if idx>=len(self.entities_data):return
        self.selected_entity=idx
        row=self.entities_data[idx]
        for key in ("x","y","z","rotation"):
            self.entity_vars[key].set(str(row.get(key,"")))

    def apply_entity_edit(self):
        if self.selected_entity is None:
            messagebox.showinfo("Editor","Selecciona una entidad de la lista.")
            return
        row=self.entities_data[self.selected_entity]
        try:
            x,y,z=[float(self.entity_vars[k].get().strip()) for k in ("x","y","z")]
            rotation=self.entity_vars["rotation"].get().strip()
            node=row["_node"]
            if row.get("_pos_el") is not None:
                self._xml_set_vector(row["_pos_el"],[x,y,z])
            elif row.get("_pos_attr"):
                node.set("position",f"{x:g}, {y:g}, {z:g}")
            else:
                raise ValueError("No se reconoce el formato XML de la posición.")
            if rotation:
                rvals=re.findall(r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?",rotation)
                if len(rvals) not in (3,4):
                    raise ValueError("La rotación debe tener 3 o 4 números, separados por coma o espacio.")
                rvals=[float(v) for v in rvals]
                if row.get("_rot_el") is not None:
                    self._xml_set_vector(row["_rot_el"],rvals)
                elif row.get("_rot_attr"):
                    node.set("rotation",", ".join(f"{v:g}" for v in rvals))
                else:
                    # Do not create a guessed rotation structure in an unknown XML schema.
                    raise ValueError("Esta entidad no contiene una etiqueta o atributo rotation editable.")
            row.update({"x":x,"y":y,"z":z,"rotation":rotation})
            self.refresh_entity_table()
            self.entity_tree.selection_set(str(self.selected_entity))
            self.status.set("Cambio aplicado en memoria. Guarda el XML para escribirlo.")
        except Exception as e:
            messagebox.showerror("Dato inválido",f"Revisa X, Y, Z y rotación.\n{e}")

    def save_entity_xml(self):
        if self.selected_entity is None:
            messagebox.showinfo("Guardar XML","Selecciona una entidad para identificar su archivo.")
            return
        path=self.entities_data[self.selected_entity]["_path"]
        tree=self.xml_trees.get(path)
        if tree is None:
            messagebox.showerror("Guardar XML","No se encontró el XML cargado.")
            return
        dest=filedialog.asksaveasfilename(defaultextension=".xml",
            initialfile=os.path.basename(path).replace(".xml","_editado.xml"),
            filetypes=[("XML","*.xml")])
        if not dest:return
        try:
            tree.write(dest,encoding="utf-8",xml_declaration=True)
            messagebox.showinfo("XML guardado",f"Se guardó una copia modificada:\n{dest}")
            self.status.set("XML editado exportado.")
        except Exception as e: messagebox.showerror("Error",str(e))

    def export_entities(self):
        if not self.workdir:
            messagebox.showinfo("Entidades","Abre una carpeta extraída o extrae los archivos accesibles primero.")
            return
        rows=self._load_entity_rows()
        if not rows:
            messagebox.showinfo("Entidades","No se encontraron entidades con posición en XML. Si tienes un mapa binario, expórtalo primero a XML con una herramienta compatible como CodeWalker.")
            return
        dest=filedialog.asksaveasfilename(defaultextension=".csv",initialfile="entidades_mapa.csv",
                                          filetypes=[("CSV","*.csv")])
        if not dest:return
        try:
            with open(dest,"w",newline="",encoding="utf-8-sig") as f:
                w=csv.DictWriter(f,fieldnames=["name","x","y","z","rotation","file"])
                w.writeheader()
                for row in rows:
                    w.writerow({k:row.get(k,"") for k in w.fieldnames})
            messagebox.showinfo("Exportación lista",f"Entidades exportadas: {len(rows)}\n{dest}")
        except Exception as e: messagebox.showerror("Error",str(e))

    def search_content(self):
        if not self.workdir:
            messagebox.showinfo("Buscar", "Primero extrae los archivos accesibles o abre una carpeta.")
            return
        win = tk.Toplevel(self)
        win.title("Buscar en el recurso")
        win.geometry("680x500")
        win.configure(bg="#101522")
        tk.Label(win, text="Nombre de archivo o texto dentro de archivos", bg="#101522",
                 fg="white", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=(14,6))
        q = tk.Entry(win, bg="#151e2e", fg="white", insertbackground="white",
                     relief="flat", font=("Segoe UI", 11))
        q.pack(fill="x", padx=14, pady=6)
        result = tk.Listbox(win, bg="#151e2e", fg="#e8edf7", selectbackground="#284d78",
                            relief="flat", font=("Consolas", 9))
        result.pack(fill="both", expand=True, padx=14, pady=10)
        paths = []
        def run_search():
            term=q.get().strip().lower()
            result.delete(0,"end"); paths.clear()
            if not term: return
            for root, dirs, files in os.walk(self.workdir):
                dirs[:] = [d for d in dirs if d not in (".git","__pycache__")]
                for fn in files:
                    full=os.path.join(root,fn); rel=os.path.relpath(full,self.workdir)
                    matched=term in fn.lower()
                    if not matched and Path(fn).suffix.lower() in TEXT_EXT:
                        try:
                            if os.path.getsize(full) <= 2_000_000:
                                with open(full,"r",encoding="utf-8",errors="ignore") as f:
                                    matched=term in f.read().lower()
                        except: pass
                    if matched:
                        paths.append(rel); result.insert("end",rel)
            if not paths: result.insert("end","Sin coincidencias.")
        def open_result(event=None):
            sel=result.curselection()
            if not sel or sel[0]>=len(paths): return
            rel=paths[sel[0]]
            for item in self.tree.get_children():
                if self.tree.item(item,"text")==rel:
                    self.tree.selection_set(item); self.open_selected(); break
            else:
                full=os.path.join(self.workdir,rel)
                try:
                    raw=open(full,"rb").read()
                    if raw[:4]==b"FXAP": raise ValueError("Archivo protegido por FXAP.")
                    if len(raw)>4_000_000: raise ValueError("Archivo demasiado grande.")
                    content=raw.decode("utf-8")
                    self.current_file=("disk",full)
                    self.editor.delete("1.0","end"); self.editor.insert("1.0",content)
                    self.tabs.select(self.tab_editor); self.status.set("Editando: "+rel)
                    win.destroy()
                except Exception as e: messagebox.showinfo("No editable",str(e))
        ttk.Button(win,text="Buscar",command=run_search).pack(anchor="e",padx=14)
        result.bind("<Double-1>",open_result)
        q.bind("<Return>",lambda e:run_search())

    def pack_zip(self):
        if not self.workdir or not os.path.isdir(self.workdir):
            messagebox.showinfo("Crear ZIP", "Primero extrae los archivos accesibles o abre una carpeta de recurso.")
            return
        dest=filedialog.asksaveasfilename(defaultextension=".zip",
            initialfile=Path(self.workdir).name+"_editado.zip",
            filetypes=[("Archivo ZIP","*.zip")])
        if not dest:return
        try:
            with zipfile.ZipFile(dest,"w",zipfile.ZIP_DEFLATED) as z:
                for root,dirs,files in os.walk(self.workdir):
                    dirs[:] = [d for d in dirs if d not in (".git","__pycache__")]
                    for fn in files:
                        full=os.path.join(root,fn)
                        rel=os.path.relpath(full,self.workdir).replace(os.sep,"/")
                        z.write(full,rel)
            self.status.set("ZIP final creado.")
            messagebox.showinfo("ZIP creado",f"Se creó el recurso editado:\n{dest}\n\nComprueba el recurso en un servidor de pruebas antes de publicarlo.")
        except Exception as e: messagebox.showerror("Error al crear ZIP",str(e))

    @staticmethod
    def fmt_size(n):
        for unit in ("B","KB","MB","GB"):
            if n<1024:return f"{n:.0f} {unit}"
            n/=1024
        return f"{n:.1f} TB"

if __name__=="__main__":
    Studio().mainloop()
