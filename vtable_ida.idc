// this dumps all the vtables from a dll file
//	this can only be run AFTER:
//	1.	class informer has been run

#include <idc.idc>

static main()
{
	auto pAddress, iIndex, pStartAddress;
	auto szFilePath, szFile, szFolderPath, szOldName, hFile;
	auto skipAmt;

	SetStatus(IDA_STATUS_WORK);

	// User selected vtable block
	pStartAddress = ScreenEA();

	//skipAmt = AskLong(1, "Number of vtable entries to ignore for indexing:");
	skipAmt = 0;

	// Request output header file
	SetStatus(IDA_STATUS_WAITING);
	if ((szFolderPath = AskStr("C:\\vtabledump\\", "Select output dump folder:")) == 0)
	{
		Message("Aborted - Bad folder name.");
		SetStatus(IDA_STATUS_READY);
		return;
	}

	auto windowsBinary = 0;
	auto searchString = "`vtable";
	pAddress = FindText(pStartAddress, SEARCH_DOWN|SEARCH_NEXT, 0, 0, searchString);

	if(pAddress == BADADDR)
	{
		searchString = "`vftable";
		pAddress = FindText(pStartAddress, SEARCH_DOWN|SEARCH_NEXT, 0, 0, searchString);

		if(pAddress == BADADDR)
		{
			Message("Aborted - Unknown binary type.");
			SetStatus(IDA_STATUS_READY);
			return;
		}

		windowsBinary = 1;
	}

	auto maxIter;
	maxIter = 1000000;
	auto iter;
	iter = 0;

	auto isValid = 1;

	while(pAddress != BADADDR && iter < maxIter)
	{
		isValid = 1;
		auto szMangledFile = Name(pAddress);
		//Message("%s\n", szMangledFile);
		//Message("%s\n", szFile);

		szOldName = szMangledFile;

		if(strstr(szMangledFile, "__ZTI") != -1 || strstr(szMangledFile, "??_7") == -1)
		{
			// this is type info!
			isValid = 0;
		}

		if(windowsBinary)
		{
			auto pos;
			while((pos = strstr(szMangledFile, "?")) != -1)
			{
				szMangledFile[pos] = "_";
			}
		}

		szFile = /*Demangle(szMangledFile, INF_LONG_DN)*/ szMangledFile;

		szFilePath = sprintf("%s%s.txt", szFolderPath, szFile);

		if(strlen(szFilePath) == 0)
		{
			Message("0 length vtable name\nSkipping.");
			isValid = 0;
			//SetStatus(IDA_STATUS_READY);
			//return;
		}
		// And create it..
		if(isValid)
		{

			if ((hFile = fopen(szFilePath, "wb")) != 0)
			{
				auto szFuncName, szFullName, BadHits;
				
				BadHits = 0;
				iIndex = 0;

				// Create the header
				if(windowsBinary)
				{
					fprintf(hFile, "// %s\r\n", szFile);
				}
				else
				{
					fprintf(hFile, "// %s\r\n", Demangle(szFile, INF_LONG_DN));
				}
				fprintf(hFile, "// Auto reconstructed from vtable block @ 0x%08X\r\n// from \"%s\", by ida_vtables.idc\r\n", pAddress, GetInputFile());
				
				/* For linux, skip the first entry */
				if (Dword(pAddress) == 0)
				{
					pAddress = pAddress + 8;
				}
				
				pAddress = pAddress + (skipAmt * 4);

				auto oneTime = 1;

				// Loop through the vtable block
				while (pAddress != BADADDR && strstr(Name(pAddress), "__ZTI") == -1 && ((windowsBinary && Name(pAddress) == "") || oneTime))
				{
					auto real_addr;
					real_addr = Dword(pAddress);
						
					szFuncName = Name(real_addr);
					if (strlen(szFuncName) == 0)
					{
						break;
					}
					else if(strstr(szFuncName, "words") != -1)
					{
						break;
					}
					else if( strstr(szFuncName, "_0") != -1)
					{
						if(strstr(szFuncName, "word") != -1)
						{
							break;
						}
					}
					szFullName = Demangle(szFuncName, INF_LONG_DN);
					if (szFullName == "")
					{
						szFullName = szFuncName;
					}
					if (strstr(szFullName, "_ZN") != -1)
					{
						fclose(hFile);
						Warning("You must toggle GCC v3.x demangled names!\r\n");
						break;
					}
					fprintf(hFile, "%d\t%s\r\n", iIndex, szFullName);
								
					pAddress = pAddress + 4;
					iIndex++;
					oneTime = 0;
				};

				pAddress = pAddress - 4;

				fclose(hFile);
				Message("Successfully wrote %d vtable entries.\r\n", iIndex);
			}
			else
			{		
				Message("** Error opening \"%s\"! Aborted **\r\n", szFilePath);
				//Warning("Error creating \"%s\"!\r\n", szFilePath);
			}

			// store the rtti hierarchy aswell

			
		}

		auto pNewAddress;
		auto line = 0;
		do 
		{
			pNewAddress = FindText(pAddress + line, SEARCH_DOWN|SEARCH_NEXT, 0, 0, searchString);
			//Message("%X\n", pAddress);
			line = line + 4;
		}
		while(pNewAddress == pAddress);
		pAddress = pNewAddress;


		iter = iter + 1;
	}
	Message("\nDone.\n\n");
	SetStatus(IDA_STATUS_READY);
}
