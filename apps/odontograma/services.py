def obtener_info_pieza(codigo_pieza):
    """
    Retorna información anatómica de la pieza según la numeración FDI.
    Ejemplo: 16 -> Molar Superior, 3 raíces.
    """
    try:
        num = int(codigo_pieza)
    except ValueError:
        return {"tipo": "desconocido", "raices": []}

    # Temporal vs Permanente
    es_temporal = (51 <= num <= 55) or (61 <= num <= 65) or (71 <= num <= 75) or (81 <= num <= 85)
    
    # Obtener el número del diente dentro de la arcada (1 a 8)
    diente = num % 10
    
    # Determinar si es superior o inferior
    cuadrante = num // 10
    es_superior = cuadrante in [1, 2, 5, 6]

    info = {
        "es_temporal": es_temporal,
        "es_superior": es_superior,
        "tipo": "desconocido",
        "raices": ["unica"],
        "caras_coronarias": ["vestibular", "palatina", "mesial", "distal", "oclusal"] if es_superior else ["vestibular", "lingual", "mesial", "distal", "oclusal"]
    }

    if diente in [1, 2, 3]:  # Incisivos y Caninos
        info["tipo"] = "anterior"
        info["raices"] = ["unica"]
        # En anteriores no hay oclusal, hay incisal
        if es_superior:
            info["caras_coronarias"] = ["vestibular", "palatina", "mesial", "distal", "incisal"]
        else:
            info["caras_coronarias"] = ["vestibular", "lingual", "mesial", "distal", "incisal"]

    elif diente in [4, 5]:  # Premolares
        info["tipo"] = "premolar"
        if es_superior and diente == 4:
            # 1er premolar superior a menudo tiene 2 raíces (vestibular y palatina)
            info["raices"] = ["vestibular", "palatina"]
        else:
            info["raices"] = ["unica"]

    elif diente in [6, 7, 8]:  # Molares
        info["tipo"] = "molar"
        if es_superior:
            info["raices"] = ["mesiovestibular", "distovestibular", "palatina"]
        else:
            info["raices"] = ["mesial", "distal"]

    return info
