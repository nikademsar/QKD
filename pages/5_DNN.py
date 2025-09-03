# requirements: pandas, pyarrow, numpy, scikit-learn, torch
import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader

# ---------- 0) konfiguracija ----------
INPUT_FOLDER  = r"C:\Users\nikde\Desktop\podatki_cv"
OUTPUT_FOLDER = r"C:\Users\nikde\Desktop\podatki_pt"

# parametri modela
TIMESTAMP_COL = None
FEATURE_COLS = ["Total Samples","Pin44 Active (1/0)","Pin45 Active (1/0)",
                "Avg Pin44 (mid points)","Avg Pin45 (mid points)"]
LABEL_COL = "Out of Normal Range"
SEQ_LEN = 30
BATCH_SIZE = 64
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# ---------- 1) CSV -> Parquet (vse datoteke v mapi) ----------
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
parquet_files = []

for file in os.listdir(INPUT_FOLDER):
    if file.lower().endswith(".csv"):
        input_path  = os.path.join(INPUT_FOLDER, file)
        base_name   = os.path.splitext(file)[0]
        output_path = os.path.join(OUTPUT_FOLDER, base_name + ".parquet")
        if not os.path.exists(output_path):
            print(f"Pretvarjam {file} ...")
            df = pd.read_csv(input_path)
            df.to_parquet(output_path, engine="pyarrow", compression="snappy")
        parquet_files.append(output_path)

# ---------- 2) Združimo vse Parquet v en DataFrame ----------
dfs = [pd.read_parquet(p) for p in parquet_files]
df = pd.concat(dfs, ignore_index=True)
df = df.reset_index(drop=True)

# ---------- 3) Split ----------
n = len(df)
train_df = df.iloc[:int(0.7*n)].copy()
val_df   = df.iloc[int(0.7*n):int(0.85*n)].copy()
test_df  = df.iloc[int(0.85*n):].copy()

# ---------- 4) Scaler ----------
scaler = StandardScaler()
scaler.fit(train_df[FEATURE_COLS])

def scale_df(mydf):
    X = scaler.transform(mydf[FEATURE_COLS])
    y = mydf[LABEL_COL].astype(np.float32).values
    return X.astype(np.float32), y

X_train, y_train = scale_df(train_df)
X_val,   y_val   = scale_df(val_df)
X_test,  y_test  = scale_df(test_df)

# ---------- 5) Sekvenčni vzorci ----------
def build_sequences(X, y, seq_len):
    Xs, ys = [], []
    for i in range(seq_len, len(X)):
        Xs.append(X[i-seq_len:i])
        ys.append(y[i])
    if len(Xs) == 0:
        return np.zeros((0,seq_len,X.shape[1]), dtype=np.float32), np.zeros((0,), dtype=np.float32)
    return np.stack(Xs), np.array(ys, dtype=np.float32)

Xtr_seq, ytr_seq = build_sequences(X_train, y_train, SEQ_LEN)
Xva_seq, yva_seq = build_sequences(X_val,   y_val,   SEQ_LEN)
Xte_seq, yte_seq = build_sequences(X_test,  y_test,  SEQ_LEN)

# ---------- 6) Dataset razredi ----------
class TabularDataset(Dataset):
    def __init__(self, X, y): self.X, self.y = X, y
    def __len__(self): return len(self.X)
    def __getitem__(self, idx): return torch.from_numpy(self.X[idx]), torch.tensor(self.y[idx])

class SequenceDataset(Dataset):
    def __init__(self, X_seq, y_seq): self.X, self.y = X_seq, y_seq
    def __len__(self): return len(self.X)
    def __getitem__(self, idx): return torch.from_numpy(self.X[idx]), torch.tensor(self.y[idx])

# loaders
tab_train_loader = DataLoader(TabularDataset(X_train, y_train), batch_size=BATCH_SIZE, shuffle=True)
tab_val_loader   = DataLoader(TabularDataset(X_val, y_val), batch_size=BATCH_SIZE)
tab_test_loader  = DataLoader(TabularDataset(X_test, y_test), batch_size=BATCH_SIZE)

seq_train_loader = DataLoader(SequenceDataset(Xtr_seq, ytr_seq), batch_size=BATCH_SIZE, shuffle=True)
seq_val_loader   = DataLoader(SequenceDataset(Xva_seq, yva_seq), batch_size=BATCH_SIZE)
seq_test_loader  = DataLoader(SequenceDataset(Xte_seq, yte_seq), batch_size=BATCH_SIZE)

# ---------- 7) Modeli ----------
class MLP(nn.Module):
    def __init__(self, in_dim):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim,128), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(128,64), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(64,1)
        )
    def forward(self,x): return self.net(x).squeeze(1)

class GRUClassifier(nn.Module):
    def __init__(self, in_dim, hidden=64, layers=1):
        super().__init__()
        self.gru = nn.GRU(in_dim, hidden, num_layers=layers, batch_first=True, bidirectional=True)
        self.head = nn.Sequential(nn.Linear(2*hidden,64), nn.ReLU(), nn.Dropout(0.2), nn.Linear(64,1))
    def forward(self,x):
        out, _ = self.gru(x)
        last = out[:, -1, :]
        return self.head(last).squeeze(1)

# izberi model
use_sequence = True
if use_sequence:
    model = GRUClassifier(in_dim=X_train.shape[1]).to(DEVICE)
    train_loader, val_loader, test_loader = seq_train_loader, seq_val_loader, seq_test_loader
else:
    model = MLP(in_dim=X_train.shape[1]).to(DEVICE)
    train_loader, val_loader, test_loader = tab_train_loader, tab_val_loader, tab_test_loader

opt = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
loss_fn = nn.BCEWithLogitsLoss()

# ---------- 8) Učenje ----------
def evaluate_auc(loader):
    model.eval()
    ys, ps = [], []
    with torch.no_grad():
        for Xb, yb in loader:
            Xb = Xb.to(DEVICE).float()
            logits = model(Xb)
            probs = torch.sigmoid(logits).cpu().numpy()
            ys.append(yb.numpy())
            ps.append(probs)
    if len(ys)==0: return None
    y_true = np.concatenate(ys)
    y_prob = np.concatenate(ps)
    try:
        return roc_auc_score(y_true, y_prob)
    except:
        return None

best_val = -np.inf
patience, wait = 7, 0
for epoch in range(1,51):
    model.train()
    for Xb, yb in train_loader:
        Xb, yb = Xb.to(DEVICE).float(), yb.to(DEVICE).float()
        opt.zero_grad()
        logits = model(Xb)
        loss = loss_fn(logits, yb)
        loss.backward(); opt.step()
    val_auc = evaluate_auc(val_loader)
    print(f"Epoch {epoch}  val_auc: {val_auc}")
    if val_auc is not None and val_auc > best_val:
        best_val = val_auc
        wait = 0
        torch.save(model.state_dict(), "best_model.pt")
    else:
        wait += 1
        if wait >= patience:
            print("Early stopping")
            break

# ---------- 9) Test ----------
if os.path.exists("best_model.pt"):
    model.load_state_dict(torch.load("best_model.pt", map_location=DEVICE))
test_auc = evaluate_auc(test_loader)
print("TEST AUC:", test_auc)
