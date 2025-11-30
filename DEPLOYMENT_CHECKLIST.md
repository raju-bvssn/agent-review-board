# 🚀 Streamlit Cloud Deployment Checklist

## ✅ Pre-Deployment (Complete)

- [x] Updated `requirements.txt` with pinned versions
- [x] Removed ollama from dependencies (cloud incompatible)
- [x] Created `.streamlit/secrets.toml` template
- [x] Added cloud environment detection (`app/utils/env.py`)
- [x] Updated provider factory to hide Ollama in cloud
- [x] Moved `st.set_page_config` to top of `streamlit_app.py`
- [x] Added cloud deployment banner
- [x] All 250 tests passing
- [x] Zero regressions

---

## 📝 Deployment Steps

### **1. Push to GitHub**

```bash
git add .
git commit -m "feat: Prepare for Streamlit Cloud deployment"
git push origin main
```

### **2. Deploy on Streamlit Cloud**

1. Go to https://share.streamlit.io/
2. Click "New app"
3. Connect GitHub repository: `raju-bvssn/agent-review-board`
4. Set main file: `streamlit_app.py`
5. Click "Deploy"

### **3. Configure Secrets**

In Streamlit Cloud dashboard:
1. Go to App Settings → Secrets
2. Paste the following with your actual API keys:

```toml
OPENAI_API_KEY="sk-..."
ANTHROPIC_API_KEY="sk-ant-..."
GEMINI_API_KEY="..."
HUGGINGFACE_API_KEY="hf_..."
```

3. Click "Save"
4. App will automatically restart

---

## ✅ Post-Deployment Verification

### **Visual Checks:**
- [ ] App loads without errors
- [ ] Sidebar shows "☁️ Running on Streamlit Cloud" banner
- [ ] No Ollama provider in LLM Settings dropdown
- [ ] All other providers visible (Mock, OpenAI, Anthropic, Gemini, HuggingFace)

### **Functional Checks:**
- [ ] Mock provider works (no API key required)
- [ ] OpenAI provider connects with valid API key
- [ ] Anthropic provider connects with valid API key
- [ ] Gemini provider connects with valid API key
- [ ] HuggingFace provider connects with valid API key
- [ ] Can start a session
- [ ] Can select models from provider
- [ ] Can run iterations
- [ ] Can approve feedback
- [ ] Liquid Glass theme displays correctly

### **Error Checks:**
- [ ] No errors in browser console
- [ ] No Python errors in logs
- [ ] No missing dependency errors
- [ ] No crashes when switching pages

---

## 🔧 Local Development Verification

### **Run Locally:**
```bash
streamlit run streamlit_app.py --server.port 8504
```

### **Local Checks:**
- [ ] No cloud banner shown
- [ ] Ollama provider visible in LLM Settings
- [ ] All 6 providers available
- [ ] Tests pass: `pytest tests/ -q`

---

## 🆘 Troubleshooting

### **Issue: App won't start**
- Check Streamlit Cloud logs for errors
- Verify `requirements.txt` syntax
- Ensure no syntax errors in Python files

### **Issue: "Module not found" error**
- Check if all dependencies are in `requirements.txt`
- Verify package names are correct
- Check for typos in import statements

### **Issue: API keys not working**
- Verify secrets are formatted correctly (no extra spaces)
- Check that keys are valid and not expired
- Ensure key names match: `OPENAI_API_KEY`, etc.

### **Issue: Ollama showing in cloud**
- Check that `app/utils/env.py` exists
- Verify `is_cloud()` function is working
- Check provider factory imports env module

---

## 📞 Support Resources

- **Streamlit Cloud Docs:** https://docs.streamlit.io/streamlit-community-cloud
- **Secrets Management:** https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management
- **App Logs:** Access via Streamlit Cloud dashboard → Logs

---

## 🎉 Success Criteria

Your deployment is successful if:

1. ✅ App loads on Streamlit Cloud URL
2. ✅ Cloud banner visible in sidebar
3. ✅ At least one provider works (Mock always works)
4. ✅ Can complete full workflow (session → iteration → review → approve)
5. ✅ No errors in logs
6. ✅ UI looks correct (Liquid Glass theme)

---

**Last Updated:** 2025-11-29  
**Phase:** 4.4 Complete  
**Status:** Ready for Deployment ✅

